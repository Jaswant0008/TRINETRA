import re
import math
from typing import Optional, Tuple, Dict, Any, List
from app.models.schemas import CoordinateData, VisualSourceTrace, ConflictFlag

# Haversine distance in meters
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class CoordinateExtractor:
    """Robust Coordinate Parser, Normalizer & Conflict Detection Engine"""

    # Decimal Degree patterns: e.g. 34.0522° N, 74.8321° E, or Lat: 34.0522, Lon: 74.8321, or 34.0522N, 74.8321E
    DD_PATTERN = re.compile(
        r'(?:lat(?:itude)?\s*[:=]?\s*)?([+-]?\d{1,2}\.\d+)\s*(?:°)?\s*([NS])?\s*[,;/ ]\s*(?:lon(?:gitude)?\s*[:=]?\s*)?([+-]?\d{1,3}\.\d+)\s*(?:°)?\s*([EW])?',
        re.IGNORECASE
    )

    # Simple coordinate pair: [34.0522, 74.8321]
    BRACKET_PATTERN = re.compile(
        r'\[\s*([+-]?\d{1,2}\.\d+)\s*,\s*([+-]?\d{1,3}\.\d+)\s*\]'
    )

    # DMS pattern: 34° 03' 08" N, 74° 49' 55" E
    DMS_PATTERN = re.compile(
        r'(\d{1,2})°\s*(\d{1,2})\'\s*([\d\.]+)"?\s*([NS])\s*[,; ]\s*(\d{1,3})°\s*(\d{1,2})\'\s*([\d\.]+)"?\s*([EW])',
        re.IGNORECASE
    )

    # Grid reference pattern: e.g. MGRS 43S DU 8492 6812 or GRID REF: 34N-74E
    GRID_PATTERN = re.compile(
        r'(?:grid\s*ref(?:erence)?|mgrs)\s*[:=]?\s*([0-9]{1,2}[A-Z]\s+[A-Z]{2}\s+[0-9\s]{4,10})',
        re.IGNORECASE
    )

    @classmethod
    def parse_coordinate_text(cls, text: str, trace: Optional[VisualSourceTrace] = None) -> Optional[CoordinateData]:
        if not text:
            return None

        # Check DMS
        dms_match = cls.DMS_PATTERN.search(text)
        if dms_match:
            d1, m1, s1, h1, d2, m2, s2, h2 = dms_match.groups()
            lat = float(d1) + float(m1)/60.0 + float(s1)/3600.0
            if h1.upper() == 'S': lat = -lat
            lon = float(d2) + float(m2)/60.0 + float(s2)/3600.0
            if h2.upper() == 'W': lon = -lon
            return CoordinateData(
                latitude=round(lat, 5),
                longitude=round(lon, 5),
                raw_text=dms_match.group(0),
                format="DMS",
                source_trace=trace
            )

        # Check Decimal Degrees
        dd_match = cls.DD_PATTERN.search(text)
        if dd_match:
            lat_val, lat_dir, lon_val, lon_dir = dd_match.groups()
            try:
                lat = float(lat_val)
                lon = float(lon_val)
                if lat_dir and lat_dir.upper() == 'S' and lat > 0: lat = -lat
                if lon_dir and lon_dir.upper() == 'W' and lon > 0: lon = -lon
                return CoordinateData(
                    latitude=round(lat, 5),
                    longitude=round(lon, 5),
                    raw_text=dd_match.group(0).strip(),
                    format="DECIMAL_DEGREES",
                    source_trace=trace
                )
            except ValueError:
                pass

        # Check Bracket format [34.0522, 74.8321]
        bracket_match = cls.BRACKET_PATTERN.search(text)
        if bracket_match:
            try:
                lat = float(bracket_match.group(1))
                lon = float(bracket_match.group(2))
                return CoordinateData(
                    latitude=round(lat, 5),
                    longitude=round(lon, 5),
                    raw_text=bracket_match.group(0),
                    format="BRACKET_DD",
                    source_trace=trace
                )
            except ValueError:
                pass

        # Check Grid Ref
        grid_match = cls.GRID_PATTERN.search(text)
        if grid_match:
            grid_str = grid_match.group(1).strip()
            # Demo synthetic converter for grid ref
            return CoordinateData(
                latitude=34.0500,
                longitude=74.8300,
                raw_text=f"MGRS {grid_str}",
                format="MGRS_GRID",
                grid_reference=grid_str,
                source_trace=trace
            )

        return None

    @classmethod
    def check_coordinate_conflict(
        cls,
        entity_name: str,
        coord_a: CoordinateData,
        source_a_name: str,
        coord_b: CoordinateData,
        source_b_name: str,
        distance_threshold_meters: float = 800.0
    ) -> Optional[ConflictFlag]:
        """Flags coordinate conflicts if distance between reports exceeds threshold (Section 9.E)"""
        dist = haversine_distance(coord_a.latitude, coord_a.longitude, coord_b.latitude, coord_b.longitude)
        if dist > distance_threshold_meters:
            desc = (
                f"Conflicting coordinates reported for entity '{entity_name}'. "
                f"Source [{source_a_name}] reported ({coord_a.latitude:.4f}, {coord_a.longitude:.4f}) while "
                f"Source [{source_b_name}] reported ({coord_b.latitude:.4f}, {coord_b.longitude:.4f}). "
                f"Discrepancy distance: {dist/1000.0:.2f} km."
            )
            return ConflictFlag(
                entity_name=entity_name,
                conflict_type="COORDINATE_MISMATCH",
                description=desc,
                source_a={
                    "source": source_a_name,
                    "latitude": coord_a.latitude,
                    "longitude": coord_a.longitude,
                    "raw": coord_a.raw_text,
                    "doc_id": coord_a.source_trace.document_name if coord_a.source_trace else "Unknown"
                },
                source_b={
                    "source": source_b_name,
                    "latitude": coord_b.latitude,
                    "longitude": coord_b.longitude,
                    "raw": coord_b.raw_text,
                    "doc_id": coord_b.source_trace.document_name if coord_b.source_trace else "Unknown"
                },
                severity="HIGH" if dist > 3000 else "MEDIUM",
                status="UNRESOLVED_FLAGGED"
            )
        return None
