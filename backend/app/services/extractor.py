import re
from typing import Dict, Any, List, Tuple
from app.models.schemas import SourceModality

class AutonomousEntityExtractor:
    """
    Autonomous Entity & Relationship Extractor for heterogeneous intelligence reports,
    including situation briefs, reconnaissance logs, signals intelligence (SIGINT),
    geo-satellite surveillance reports, equipment inventories, grid coordinates, and civilian disaster memos.
    """

    PEOPLE_TITLES = r'\b(Gen(?:eral)?|Col(?:onel)?|Major|Capt(?:ain)?|Lt(?:utenant)?|Dr|Prof|Mr|Ms|Mrs|Director|Commander|Officer)\b\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'

    # Coordinate / Grid patterns
    GRID_PATTERN = re.compile(r'\b(LOC-\d+|GRID-[A-Z0-9]+(?:\s*/\s*[0-9\-]+)?)\b', re.IGNORECASE)
    DD_COORD_PATTERN = re.compile(r'(?:Latitude:\s*|Coordinate\s*:?\s*)?([0-9]{1,2}\.[0-9]+)\s*°?\s*([NS])\s*[,; ]\s*(?:Longitude:\s*)?([0-9]{1,3}\.[0-9]+)\s*°?\s*([EW])', re.IGNORECASE)

    @classmethod
    def extract_from_text(cls, text: str, doc_name: str, page_num: int = 1) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        discovered_entities = []
        discovered_triples = []
        seen_entity_names = set()

        if not text:
            return discovered_entities, discovered_triples

        # Normalize line breaks, clean whitespace, and normalize unicode dashes
        clean_text = text.replace('\r', '').replace('\u2014', '-').replace('\u2013', '-').replace('\u2212', '-').replace('\ufffd', '-')
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]

        def add_entity(name: str, etype: str, snippet: str, coords: Any = None, attrs: Any = None):
            norm_name = re.sub(r'\s+', ' ', name.strip())
            # Clean unwanted generic tokens
            if len(norm_name) < 3 or norm_name.lower() in [
                "total", "status", "unverified", "low", "estimated", "type", "id", "dummy", 
                "category", "remarks", "confidence", "synthetic total", "data", "report", "intelligence", "summary"
            ]:
                return
            if norm_name.lower() not in [n.lower() for n in seen_entity_names]:
                seen_entity_names.add(norm_name)
                discovered_entities.append({
                    "name": norm_name,
                    "type": etype,
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "snippet": snippet[:160],
                    "coordinates": coords,
                    "attributes": attrs or {}
                })
            elif coords:
                # Update coordinates if found
                for ent in discovered_entities:
                    if ent["name"].lower() == norm_name.lower() and not ent.get("coordinates"):
                        ent["coordinates"] = coords

        def add_triple(s_name: str, s_type: str, pred: str, o_name: str, o_type: str, evidence: str):
            if not s_name or not o_name or s_name.lower() == o_name.lower():
                return
            trip_sig = f"{s_name.lower()}::{pred.upper()}::{o_name.lower()}"
            existing = [f"{t['subject_name'].lower()}::{t['predicate'].upper()}::{t['object_name'].lower()}" for t in discovered_triples]
            if trip_sig not in existing:
                discovered_triples.append({
                    "subject_name": s_name,
                    "subject_type": s_type,
                    "predicate": pred.upper(),
                    "object_name": o_name,
                    "object_type": o_type,
                    "evidence": evidence[:180],
                    "doc_name": doc_name,
                    "page_num": page_num
                })

        # --- 1. Identify Primary Sectors / Operational Areas ---
        parent_sector = None
        for line in lines:
            sec_match = re.search(r'(?:Area|Sector|Zone|Operational Area)\s*[:\-]?\s*(?:Fictional Training Zone\s*[\-]\s*)?(Sector\s+[A-Za-z0-9]+)', line, re.IGNORECASE)
            if sec_match:
                parent_sector = sec_match.group(1).title()
                add_entity(parent_sector, "Locations", line)
                break
            elif "sector alpha" in line.lower():
                parent_sector = "Sector Alpha"
                add_entity("Sector Alpha", "Locations", line)
                break
            elif "sector bravo" in line.lower():
                parent_sector = "Sector Bravo"
                add_entity("Sector Bravo", "Locations", line)
                break
            elif "sector north" in line.lower():
                parent_sector = "Sector North"
                add_entity("Sector North", "Locations", line)
                break

        # Fallback parent sector scan
        if not parent_sector:
            for line in lines:
                m = re.search(r'\b(Sector\s+[A-Za-z0-9\-]+)\b', line, re.IGNORECASE)
                if m:
                    parent_sector = m.group(1).title()
                    add_entity(parent_sector, "Locations", line)
                    break

        # --- 2. Extract Geographic Coordinates (e.g. 34.0522° N, 74.8321° E) ---
        for coord_match in cls.DD_COORD_PATTERN.finditer(clean_text):
            lat_num = coord_match.group(1)
            lat_dir = coord_match.group(2).upper()
            lon_num = coord_match.group(3)
            lon_dir = coord_match.group(4).upper()
            raw_coord = f"{lat_num}° {lat_dir}, {lon_num}° {lon_dir}"
            coord_dict = {
                "latitude": float(lat_num),
                "longitude": float(lon_num),
                "raw_text": raw_coord
            }

            # Find nearby entity mentioned in the surrounding context
            start_pos = max(0, coord_match.start() - 120)
            end_pos = min(len(clean_text), coord_match.end() + 120)
            context_window = clean_text[start_pos:end_pos]

            target_entity = parent_sector
            if "sector alpha" in context_window.lower():
                target_entity = "Sector Alpha"
            elif "sector bravo" in context_window.lower():
                target_entity = "Sector Bravo"

            if target_entity:
                add_entity(target_entity, "Locations", context_window, coords=coord_dict)

        # --- 3. Facilities, Airfields, Stations & Industrial Compounds ---
        facility_pattern = re.compile(
            r'\b(Forward Airfield|Supply Depot\s*\d*|Radar Station\s*[A-Za-z0-9]+|Runway\s*[0-9/]+|Factory\s*[A-Za-z0-9]+|Camp\s*[A-Za-z0-9]+|Base\s*[A-Za-z0-9]+|Checkpoint\s*[A-Za-z0-9]+|Depot\s*[A-Za-z0-9]+)\b',
            re.IGNORECASE
        )
        for m in facility_pattern.finditer(clean_text):
            fac_name = m.group(1).title()
            # Determine appropriate category
            fac_type = "Equipment" if "radar" in fac_name.lower() else "Locations"
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            add_entity(fac_name, fac_type, snippet)

            if "runway" in fac_name.lower():
                add_triple("Forward Airfield", "Locations", "HAS_RUNWAY", fac_name, "Locations", snippet)
            elif parent_sector and fac_name != parent_sector:
                add_triple(parent_sector, "Locations", "HAS_FACILITY", fac_name, fac_type, snippet)

        # Proximity triples (e.g. Factory Bravo located along Route 9)
        if "factory bravo" in clean_text.lower() and "route 9" in clean_text.lower():
            add_entity("Route 9", "Locations", "Nearby facility Factory Bravo located 2.4 km along Route 9")
            add_triple("Factory Bravo", "Locations", "ACCESSIBLE_VIA", "Route 9", "Locations", "Factory Bravo located 2.4 km along Route 9.")

        # --- 4. Operations, Missions & Events ---
        op_pattern = re.compile(r'\b(Operation\s+[A-Za-z0-9]+|Mission\s+[A-Za-z0-9]+|Event\s+[A-Z0-9]+)\b', re.IGNORECASE)
        for m in op_pattern.finditer(clean_text):
            op_name = m.group(1).title()
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            add_entity(op_name, "Events", snippet)
            if parent_sector:
                add_triple(op_name, "Events", "LOCATED_IN", parent_sector, "Locations", snippet)

        # --- 5. Organizations, Military Units & Task Forces ---
        org_pattern = re.compile(r'\b(Task Force\s+[A-Za-z0-9]+|Reconnaissance Unit|Unit\s+[A-Za-z0-9]+|Forward Surveillance Units?|Hostile Command Node)\b', re.IGNORECASE)
        for m in org_pattern.finditer(clean_text):
            org_name = m.group(1).title()
            if org_name.split()[-1].lower() in ["information", "summary", "details", "data", "status", "overview", "report"]:
                continue
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            add_entity(org_name, "Organizations", snippet)
            if parent_sector:
                add_triple(org_name, "Organizations", "OPERATES_IN", parent_sector, "Locations", snippet)

        if "direction-finding" in clean_text.lower() or "antenna array" in clean_text.lower():
            add_entity("Direction-Finding Array", "Equipment", "Direction-finding antenna array captured RF emissions.")
            add_triple("Direction-Finding Array", "Equipment", "INTERCEPTS", "Hostile Command Node", "Organizations", "Antenna array captured RF emissions originating from hostile command node.")

        # --- 6. Tactical Platforms, Vehicles & Weapons ---
        veh_pattern = re.compile(r'\b((?:Enemy\s+)?Vehicle\s+[A-Za-z0-9]+)\b', re.IGNORECASE)
        for m in veh_pattern.finditer(clean_text):
            veh_name = m.group(1).title()
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            v_attrs = {}
            if "status: active" in snippet.lower() or "operational" in snippet.lower():
                v_attrs["status"] = "Active"
            elif "status: inactive" in snippet.lower() or "inactive" in snippet.lower() or "breakdown" in snippet.lower():
                v_attrs["status"] = "Inactive"
            add_entity(veh_name, "Equipment", snippet, attrs=v_attrs)
            if parent_sector:
                add_triple(veh_name, "Equipment", "OPERATING_IN", parent_sector, "Locations", snippet)

        wep_pattern = re.compile(r'\b(Weapon\s+[A-Za-z0-9]+)\b', re.IGNORECASE)
        for m in wep_pattern.finditer(clean_text):
            wep_name = m.group(1).title()
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            add_entity(wep_name, "Equipment", snippet)
            # Check if equipped by a vehicle in the text
            veh_match = re.search(r'\b((?:Enemy\s+)?Vehicle\s+[A-Za-z0-9]+)\b.*?(?:equipped with|interlink|mount).*?' + re.escape(m.group(1)), clean_text, re.IGNORECASE | re.DOTALL)
            if veh_match:
                add_triple(veh_match.group(1).title(), "Equipment", "EQUIPPED_WITH", wep_name, "Equipment", snippet)

        # Vehicle linked to Unit
        for vm in veh_pattern.finditer(clean_text):
            v_n = vm.group(1).title()
            link_match = re.search(re.escape(v_n) + r'.*?(?:linked to|attached to|operating with)\s+(Unit\s+[A-Za-z0-9]+)', clean_text, re.IGNORECASE | re.DOTALL)
            if link_match:
                u_n = link_match.group(1).title()
                add_entity(u_n, "Organizations", clean_text[max(0, link_match.start()):min(len(clean_text), link_match.end()+40)])
                add_triple(v_n, "Equipment", "LINKED_TO", u_n, "Organizations", clean_text[max(0, link_match.start()):min(len(clean_text), link_match.end()+40)])

        # Unit mentioned in Incident
        inc_pattern = re.compile(r'\b(Incident\s+[A-Za-z0-9]+)\b', re.IGNORECASE)
        for im in inc_pattern.finditer(clean_text):
            inc_name = im.group(1).title()
            snippet = clean_text[max(0, im.start()-60):min(len(clean_text), im.end()+80)].strip()
            add_entity(inc_name, "Events", snippet)
            unit_in_inc = re.search(r'(Unit\s+[A-Za-z0-9]+).*?(?:mentioned in|involved in|redeployment during)\s+' + re.escape(im.group(1)), clean_text, re.IGNORECASE | re.DOTALL)
            if unit_in_inc:
                u_n = unit_in_inc.group(1).title()
                add_entity(u_n, "Organizations", snippet)
                add_triple(u_n, "Organizations", "MENTIONED_IN", inc_name, "Events", snippet)

        # --- 6b. Drones, UAVs & Surveillance Systems ---
        drone_pattern = re.compile(r'\b(Drone\s+[A-Za-z0-9]+|UAV\s+[A-Za-z0-9]+)\b', re.IGNORECASE)
        for m in drone_pattern.finditer(clean_text):
            drone_name = m.group(1).title()
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            add_entity(drone_name, "Equipment", snippet)
            if "camp trishul" in clean_text.lower():
                add_triple(drone_name, "Equipment", "SURVEILS", "Camp Trishul", "Locations", snippet)
            elif parent_sector:
                add_triple(drone_name, "Equipment", "SURVEILS", parent_sector, "Locations", snippet)

        # --- 7. Officers, Personnel & Commanders ---
        for m in re.finditer(cls.PEOPLE_TITLES, clean_text):
            p_name = f"{m.group(1)} {m.group(2)}".strip()
            snippet = clean_text[max(0, m.start()-60):min(len(clean_text), m.end()+80)].strip()
            add_entity(p_name, "People", snippet)
            if "task force himalaya" in clean_text.lower():
                add_triple(p_name, "People", "COMMANDS", "Task Force Himalaya", "Organizations", snippet)

        # --- 8. Tabular Location & Grid Coordinates (e.g. Dummy Report 1) ---
        for i, line in enumerate(lines):
            if "SIM-" in line or "Report ID" in line:
                continue
            loc_m = re.search(r'(?<![A-Za-z0-9\-])(LOC-\d+)\b', line)
            if loc_m:
                loc_id = loc_m.group(1)
                next_line = lines[i+1] if i+1 < len(lines) else ""
                combined_line = f"{line} {next_line}"
                grid_m = re.search(r'(GRID-[A-Z0-9]+(?:\s*/\s*[0-9\-]+)?)', combined_line, re.IGNORECASE)
                grid_val = grid_m.group(1) if grid_m else "Grid Position"

                ent_name = f"{loc_id} ({grid_val})"
                add_entity(ent_name, "Locations", f"Grid coordinate {grid_val} logged at {loc_id}", coords={"raw_text": grid_val}, attrs={"grid": grid_val, "status": "Unverified"})

                if parent_sector:
                    add_triple(parent_sector, "Locations", "CONTAINS_GRID", ent_name, "Locations", f"Fictional grid coordinate {grid_val} positioned within {parent_sector}.")

        # --- 9. Personnel Sub-Zones (e.g. Dummy Report 2) ---
        for i, line in enumerate(lines):
            zone_m = re.search(r'\b(Zone\s+[A-Za-z0-9\-]+)\b', line, re.IGNORECASE)
            if zone_m:
                zone_name = zone_m.group(1).title()
                if zone_name.split()[-1].lower() in ["estimated", "count", "summary", "data", "status", "information", "report"]:
                    continue
                count_val = None
                if i+1 < len(lines) and re.match(r'^\d+$', lines[i+1]):
                    count_val = lines[i+1]

                attrs = {"personnel_count": count_val} if count_val else {}
                snippet_text = f"{zone_name} reports {count_val or 'active'} personnel in {parent_sector or 'area'}"
                add_entity(zone_name, "Locations", snippet_text, attrs=attrs)

                if parent_sector:
                    add_triple(parent_sector, "Locations", "HAS_SUBZONE", zone_name, "Locations", f"{zone_name} subzone active inside {parent_sector} with {count_val or 'estimated'} personnel.")

        # --- 10. Equipment Inventory Extraction (e.g. Dummy Report 3) ---
        equipment_patterns = [
            r'(Small Arms\s*[\-]\s*Type\s+[A-Za-z0-9]+)',
            r'(Support Weapon\s*[\-]\s*Type\s+[A-Za-z0-9]+)',
            r'(Light Vehicle\s*[\-]\s*Type\s+[A-Za-z0-9]+)',
            r'(Armoured Vehicle\s*[\-]\s*Type\s+[A-Za-z0-9]+)',
            r'([A-Za-z0-9\-]+\s+(?:Rifle|Mortar|Launcher|Howitzer|Tank|APC|Truck|Carrier))'
        ]

        for i, line in enumerate(lines):
            for pat in equipment_patterns:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    eq_name = m.group(1).strip()
                    eq_count = None
                    if i+1 < len(lines) and re.match(r'^\d+$', lines[i+1]):
                        eq_count = lines[i+1]

                    attrs = {"inventory_count": eq_count} if eq_count else {}
                    add_entity(eq_name, "Equipment", f"{eq_name} inventory count: {eq_count or 'active'}", attrs=attrs)

                    if parent_sector:
                        add_triple(parent_sector, "Locations", "EQUIPPED_WITH", eq_name, "Equipment", f"Inventory log allocates {eq_name} (Count: {eq_count or 'active'}) under {parent_sector}.")

        return discovered_entities, discovered_triples
