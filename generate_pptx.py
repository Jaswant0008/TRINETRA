import os
import sys
import shutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml import parse_xml

# =============================================================================
# TRINETRA — DEFENCE-TECH PRESENTATION GENERATOR (MILITARY GREEN & PRACTICAL ARROWS)
# =============================================================================

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Paths to generated defence visuals
    IMG_DIR = r"d:\TRINETRA\assets\images"
    IMG_HERO_BG = os.path.join(IMG_DIR, "hero_jet_bg.jpg")
    IMG_TANK_BG = os.path.join(IMG_DIR, "tactical_tank_bg.jpg")
    IMG_OPS_BG = os.path.join(IMG_DIR, "command_centre_bg.jpg")
    IMG_UI = os.path.join(IMG_DIR, "ui_mockup.jpg")
    IMG_TRICOLOUR_BG = os.path.join(IMG_DIR, "closing_tricolour_bg.jpg")

    # =========================================================================
    # MILITARY GREEN & TACTICAL PALETTE
    # =========================================================================
    C_BG_MILITARY = RGBColor(18, 27, 20)       # #121b14 Deep Military Tactical Olive/Green
    C_CARD_BASE = RGBColor(27, 42, 30)         # #1b2a1e Tactical Olive Drab Card
    C_CARD_OVERLAY = RGBColor(22, 34, 25)      # #162219 Deep Tactical Camo Surface
    C_CARD_DARK = RGBColor(15, 23, 17)         # #0f1711 Shadow Tactical Inset
    C_BORDER_SUBTLE = RGBColor(46, 70, 52)     # #2e4634 Muted Military Olive Border
    C_BORDER_ACCENT = RGBColor(74, 222, 128)   # #4ade80 High-Visibility Spec-Ops Green
    C_CAMO_OLIVE = RGBColor(107, 142, 78)      # #6b8e4e Field Olive / Khaki Green
    C_GOLD = RGBColor(245, 158, 11)            # #f59e0b Insignia Brass Gold / Amber
    C_GOLD_LIGHT = RGBColor(254, 215, 170)     # #fed7aa Soft Amber
    C_TACTICAL_CYAN = RGBColor(45, 212, 191)   # #2dd4bf Night-Vision Mint / Cyan
    C_RED = RGBColor(239, 68, 68)              # #ef4444 Conflict / Threat Red
    C_WHITE = RGBColor(255, 255, 255)          # Pure White
    C_OFF_WHITE = RGBColor(241, 245, 249)      # #f1f5f9 Technical Crisp White
    C_MUTED = RGBColor(163, 184, 163)          # #a3b8a3 Tactical Camo Muted Text
    C_DIM = RGBColor(91, 115, 94)              # #5b735e Dim Stencil Green

    # -------------------------------------------------------------------------
    # OpenXML Helper Functions (Directional Slide Transitions)
    # -------------------------------------------------------------------------
    def apply_slide_transition(slide, trans_type="wipe", direction="r"):
        """Injects native PowerPoint transition XML into slide element in valid OpenXML sequence.
        Using directional wipe (sweep right) aligns naturally with the practical arrow flow.
        """
        sld = slide._element
        if trans_type == "wipe":
            tr_xml = f'<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:wipe dir="{direction}"/></p:transition>'
        elif trans_type == "push":
            tr_xml = f'<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:push dir="{direction}"/></p:transition>'
        elif trans_type == "morph":
            tr_xml = '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:p15="http://schemas.microsoft.com/office/powerpoint/2012/main" spd="med"><p15:morph/></p:transition>'
        elif trans_type == "fade":
            tr_xml = '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:fade/></p:transition>'
        else:
            tr_xml = '<p:transition xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" spd="med"><p:fade/></p:transition>'

        tr_elem = parse_xml(tr_xml)
        clrMapOvr = sld.find('{http://schemas.openxmlformats.org/presentationml/2006/main}clrMapOvr')
        if clrMapOvr is not None:
            clrMapOvr.addnext(tr_elem)
        else:
            cSld = sld.find('{http://schemas.openxmlformats.org/presentationml/2006/main}cSld')
            if cSld is not None:
                cSld.addnext(tr_elem)
            else:
                sld.append(tr_elem)

    # -------------------------------------------------------------------------
    # Reusable Slide Components (Military Green Styling)
    # -------------------------------------------------------------------------
    def set_solid_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG_MILITARY
        bg.line.fill.background()

        # Top micro accent line: Spec-Ops Green
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.04))
        top_bar.fill.solid()
        top_bar.fill.fore_color.rgb = C_BORDER_ACCENT
        top_bar.line.fill.background()

        # Bottom micro subtle border
        bot_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(7.46), Inches(13.333), Inches(0.04))
        bot_bar.fill.solid()
        bot_bar.fill.fore_color.rgb = C_BORDER_SUBTLE
        bot_bar.line.fill.background()

    def add_header(slide, title, category="TRINETRA // DEFENCE INTELLIGENCE PLATFORM", slide_num=None):
        # Category label + optional slide counter
        cat_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.4), Inches(10.0), Inches(0.35))
        tf_c = cat_box.text_frame
        tf_c.word_wrap = True
        p_c = tf_c.paragraphs[0]
        p_c.text = category.upper()
        p_c.font.size = Pt(10)
        p_c.font.bold = True
        p_c.font.color.rgb = C_GOLD
        p_c.font.name = "Consolas"

        if slide_num:
            num_box = slide.shapes.add_textbox(Inches(11.2), Inches(0.4), Inches(1.3), Inches(0.35))
            tf_n = num_box.text_frame
            p_n = tf_n.paragraphs[0]
            p_n.alignment = PP_ALIGN.RIGHT
            p_n.text = f"{slide_num:02d} / 10"
            p_n.font.size = Pt(10)
            p_n.font.bold = True
            p_n.font.color.rgb = C_DIM
            p_n.font.name = "Consolas"

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.72), Inches(11.5), Inches(0.75))
        tf_t = title_box.text_frame
        p_t = tf_t.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(26)
        p_t.font.bold = True
        p_t.font.color.rgb = C_WHITE
        p_t.font.name = "Arial"

    def add_card(slide, left, top, width, height, bg_color=C_CARD_BASE, border_color=C_BORDER_SUBTLE):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.2)
        return card

    # -------------------------------------------------------------------------
    # Practical Arrow & Process Flow Components
    # -------------------------------------------------------------------------
    def add_arrow_pill(slide, left, top, width, height, color=C_BORDER_ACCENT):
        """Draws a clean, practical tactical arrow shape."""
        arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, height)
        arr.fill.solid()
        arr.fill.fore_color.rgb = color
        arr.line.fill.background()
        return arr

    def add_chevron_pill(slide, left, top, width, height, color=C_BORDER_ACCENT):
        """Draws a practical tactical chevron shape for flow continuity."""
        chv = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, left, top, width, height)
        chv.fill.solid()
        chv.fill.fore_color.rgb = color
        chv.line.fill.background()
        return chv

    def add_down_arrow(slide, left, top, width, height, color=C_BORDER_ACCENT):
        """Draws a clean tactical downward arrow."""
        arr = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, left, top, width, height)
        arr.fill.solid()
        arr.fill.fore_color.rgb = color
        arr.line.fill.background()
        return arr

    def add_relation_arrow(slide, left, top, width, height, label=None, color=C_BORDER_ACCENT, text_color=C_GOLD):
        """Practical entity-relationship arrow with a centered semantic badge."""
        arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, height)
        arr.fill.solid()
        arr.fill.fore_color.rgb = color
        arr.line.fill.background()
        if label:
            lbl_w = Inches(1.5)
            lbl_h = Inches(0.24)
            lbl_x = left + (width - lbl_w) / 2
            lbl_y = top - Inches(0.28)
            lbl_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, lbl_x, lbl_y, lbl_w, lbl_h)
            lbl_box.fill.solid()
            lbl_box.fill.fore_color.rgb = C_CARD_DARK
            lbl_box.line.color.rgb = color
            lbl_box.line.width = Pt(0.8)
            tf = lbl_box.text_frame
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            p.text = label.upper()
            p.font.size = Pt(8)
            p.font.bold = True
            p.font.color.rgb = text_color
            p.font.name = "Consolas"
        return arr

    print("Building 10 Redesigned Military Green Defence-Tech Slides with Practical Arrows & Transitions...")

    # =========================================================================
    # SLIDE 1 — TITLE / COVER (PROBLEM STATEMENT 05)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    apply_slide_transition(s1, "fade")

    if os.path.exists(IMG_HERO_BG):
        s1.shapes.add_picture(IMG_HERO_BG, 0, 0, Inches(13.333), Inches(7.5))
        # Military green tactical darkening tint overlay
        overlay = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        overlay.fill.solid()
        overlay.fill.fore_color.rgb = C_BG_MILITARY
        # Line background
        overlay.line.fill.background()
    else:
        set_solid_background(s1)

    # Hero Center Glass Card (Military Olive)
    hero_card = add_card(s1, Inches(1.8), Inches(1.0), Inches(9.733), Inches(5.5), C_CARD_BASE, C_BORDER_SUBTLE)

    # Top Pill Badge
    top_badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.2), Inches(1.25), Inches(6.933), Inches(0.38))
    top_badge.fill.solid()
    top_badge.fill.fore_color.rgb = C_CARD_DARK
    top_badge.line.color.rgb = C_GOLD
    top_badge.line.width = Pt(0.8)
    tf_tb = top_badge.text_frame
    tf_tb.vertical_anchor = MSO_ANCHOR.MIDDLE
    ptb = tf_tb.paragraphs[0]
    ptb.alignment = PP_ALIGN.CENTER
    ptb.text = "PROBLEM STATEMENT 05  •  INTERNAL AGENTIC AI HACKATHON"
    ptb.font.size = Pt(11)
    ptb.font.bold = True
    ptb.font.color.rgb = C_GOLD
    ptb.font.name = "Consolas"

    # Tactical Emblem Ring
    logo_box = add_card(s1, Inches(5.966), Inches(1.85), Inches(1.4), Inches(1.4), C_CARD_DARK, C_BORDER_ACCENT)
    tf_lb = logo_box.text_frame
    tf_lb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_lb = tf_lb.paragraphs[0]
    p_lb.alignment = PP_ALIGN.CENTER
    p_lb.text = "◈"
    p_lb.font.size = Pt(44)
    p_lb.font.color.rgb = C_BORDER_ACCENT

    # Main Project Title Box
    h_box = s1.shapes.add_textbox(Inches(2.0), Inches(3.35), Inches(9.333), Inches(2.4))
    tf_h = h_box.text_frame
    tf_h.word_wrap = True

    ph1 = tf_h.paragraphs[0]
    ph1.alignment = PP_ALIGN.CENTER
    ph1.text = "TRINETRA"
    ph1.font.size = Pt(56)
    ph1.font.bold = True
    ph1.font.color.rgb = C_WHITE
    ph1.font.name = "Arial"

    ph2 = tf_h.add_paragraph()
    ph2.alignment = PP_ALIGN.CENTER
    ph2.text = "Multimodal Intelligence Fusion System"
    ph2.font.size = Pt(20)
    ph2.font.bold = True
    ph2.font.color.rgb = C_BORDER_ACCENT
    ph2.font.name = "Arial"

    ph3 = tf_h.add_paragraph()
    ph3.alignment = PP_ALIGN.CENTER
    ph3.text = "“From Fragmented Information to Strategic Insight.”"
    ph3.font.size = Pt(16)
    ph3.font.italic = True
    ph3.font.color.rgb = C_GOLD
    ph3.font.name = "Georgia"

    # Meta Tag Footer inside Card
    h_meta = s1.shapes.add_textbox(Inches(2.0), Inches(5.7), Inches(9.333), Inches(0.55))
    tf_hm = h_meta.text_frame
    phm = tf_hm.paragraphs[0]
    phm.alignment = PP_ALIGN.CENTER
    phm.text = "Agentic AI Knowledge Graph Builder  •  Military-Grade Intelligence Fusion Platform"
    phm.font.size = Pt(11)
    phm.font.bold = True
    phm.font.color.rgb = C_MUTED
    phm.font.name = "Consolas"

    # =========================================================================
    # SLIDE 2 — THE INFORMATION GAP (PRACTICAL ARROW TRANSITION)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_solid_background(s2)
    apply_slide_transition(s2, "wipe", "r")
    add_header(s2, "Fragmented information. Disconnected knowledge.", "THE INFORMATION GAP", 2)

    # Statement Box
    st2 = s2.shapes.add_textbox(Inches(0.9), Inches(1.45), Inches(11.5), Inches(0.45))
    tf_st2 = st2.text_frame
    p_st2 = tf_st2.paragraphs[0]
    p_st2.text = "“Critical intelligence exists across scattered reports — but remains disconnected without automated fusion.”"
    p_st2.font.size = Pt(14)
    p_st2.font.italic = True
    p_st2.font.color.rgb = C_GOLD_LIGHT

    # 3 Distinct Problem Cards
    col_w2 = Inches(3.64)
    col_h2 = Inches(3.2)
    gap2 = Inches(0.3)
    start_x2 = Inches(0.9)
    top_y2 = Inches(2.0)

    gap_cards = [
        ("DIFFERENT NAMES", "The same entity may appear under different names across isolated reports.\n\n• Aliases & spelling variations\n• Inconsistent call-signs\n• Siloed records stay unlinked", C_BORDER_ACCENT),
        ("HIDDEN RELATIONSHIPS", "Links and connections are difficult to discover across multi-source reports.\n\n• Cross-document blind spots\n• Disjointed unit affiliations\n• Isolated observations hide threats", C_GOLD),
        ("MANUAL ANALYSIS", "Cross-report review is time-consuming, manual, and operationally vulnerable.\n\n• 80% time spent sorting memos\n• High risk of missed contradictions\n• Slow reaction to active developments", C_RED)
    ]

    for i, (ctitle, cdesc, ccolor) in enumerate(gap_cards):
        cx = start_x2 + i * (col_w2 + gap2)
        card = add_card(s2, cx, top_y2, col_w2, col_h2, C_CARD_BASE, ccolor)
        tf_c = card.text_frame
        tf_c.margin_left = Inches(0.25)
        tf_c.margin_top = Inches(0.25)
        tf_c.margin_right = Inches(0.25)

        p1 = tf_c.paragraphs[0]
        p1.text = f"0{i+1} // {ctitle}"
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = ccolor
        p1.font.name = "Consolas"

        p2 = tf_c.add_paragraph()
        p2.text = f"\n{cdesc}"
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_OFF_WHITE

    # Practical Flow Arrow Banner at Bottom (Replacing raw text)
    # SCATTERED REPORTS + DISCONNECTED NODES → FRAGMENTED INFORMATION → DISCONNECTED KNOWLEDGE
    bot_y2 = Inches(5.45)
    banner_bg = add_card(s2, Inches(0.9), bot_y2, Inches(11.533), Inches(1.35), C_CARD_DARK, C_BORDER_SUBTLE)

    tf_bb = banner_bg.text_frame
    tf_bb.margin_top = Inches(0.12)
    p_bh = tf_bb.paragraphs[0]
    p_bh.alignment = PP_ALIGN.CENTER
    p_bh.text = "THE ROOT CAUSE CASCADE"
    p_bh.font.size = Pt(9)
    p_bh.font.bold = True
    p_bh.font.color.rgb = C_DIM
    p_bh.font.name = "Consolas"

    # Practical Arrow Pipeline Stages inside the bottom banner
    f_items = [
        ("SCATTERED REPORTS", C_MUTED),
        ("DISCONNECTED NODES", C_GOLD),
        ("FRAGMENTED INFORMATION", C_RED),
        ("DISCONNECTED KNOWLEDGE", C_RED)
    ]
    f_w = Inches(2.2)
    f_h = Inches(0.65)
    f_y = Inches(5.9)
    f_start = Inches(1.2)
    f_arr_w = Inches(0.55)
    f_gap = Inches(0.15)

    for i, (item_text, item_col) in enumerate(f_items):
        item_x = f_start + i * (f_w + f_arr_w + f_gap * 2)
        # Step block
        sbox = add_card(s2, item_x, f_y, f_w, f_h, C_CARD_BASE, item_col)
        tf_s = sbox.text_frame
        tf_s.vertical_anchor = MSO_ANCHOR.MIDDLE
        ps = tf_s.paragraphs[0]
        ps.alignment = PP_ALIGN.CENTER
        ps.text = item_text
        ps.font.bold = True
        ps.font.size = Pt(9)
        ps.font.color.rgb = item_col
        ps.font.name = "Consolas"

        if i < len(f_items) - 1:
            arr_x = item_x + f_w + f_gap
            add_arrow_pill(s2, arr_x, f_y + Inches(0.2), f_arr_w, Inches(0.24), C_BORDER_ACCENT)

    # =========================================================================
    # SLIDE 3 — THE TRINETRA SOLUTION (8-STAGE PIPELINE WITH PRACTICAL ARROWS)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_solid_background(s3)
    apply_slide_transition(s3, "wipe", "r")
    add_header(s3, "From reports to connected, queryable insight", "THE TRINETRA SOLUTION", 3)

    # Subtitle statement
    st3 = s3.shapes.add_textbox(Inches(0.9), Inches(1.45), Inches(11.5), Inches(0.45))
    tf_st3 = st3.text_frame
    p_st3 = tf_st3.paragraphs[0]
    p_st3.text = "“TRINETRA converts multiple unstructured reports into one connected, queryable Knowledge Graph.”"
    p_st3.font.size = Pt(15)
    p_st3.font.bold = True
    p_st3.font.color.rgb = C_BORDER_ACCENT

    # 8-Stage Pipeline Cards (user's PDF 1-8 exact stages)
    pipeline_8 = [
        ("MULTIPLE\nREPORTS", "PDF, DOCX, TXT\n& raw imagery"),
        ("DOCUMENT\nPROCESSING", "OCR & layout\nsegmentation"),
        ("ENTITY & REL\nEXTRACTION", "Autonomous zero-\nshot NER triples"),
        ("ENTITY\nRESOLUTION", "Syntactic alias\nclustering"),
        ("INFORMATION\nFUSION", "Multi-source merge\n& conflict check"),
        ("KNOWLEDGE\nGRAPH", "Connected RDF\nsemantic network"),
        ("NATURAL-LANG\nQUERY", "GraphRAG multi-\nhop reasoning"),
        ("ANSWER + SOURCE\nEVIDENCE", "Grounded answer\nwith citations")
    ]

    p8_w = Inches(1.18)
    p8_arr = Inches(0.22)
    p8_gap = Inches(0.04)
    p8_top = Inches(2.15)
    p8_start_x = Inches(0.9)

    for i, (stitle, sdesc) in enumerate(pipeline_8):
        cx = p8_start_x + i * (p8_w + p8_arr + p8_gap * 2)
        is_graph = (i == 5)
        is_end = (i == 7)
        bg = RGBColor(35, 58, 40) if is_graph else (RGBColor(38, 52, 30) if is_end else C_CARD_BASE)
        brd = C_BORDER_ACCENT if (is_graph or is_end) else C_BORDER_SUBTLE

        sc = add_card(s3, cx, p8_top, p8_w, Inches(2.9), bg, brd)
        tf_s = sc.text_frame
        tf_s.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_s.margin_left = tf_s.margin_right = Inches(0.06)

        p_idx = tf_s.paragraphs[0]
        p_idx.alignment = PP_ALIGN.CENTER
        p_idx.text = f"0{i+1}"
        p_idx.font.size = Pt(11)
        p_idx.font.bold = True
        p_idx.font.color.rgb = C_GOLD
        p_idx.font.name = "Consolas"

        p_name = tf_s.add_paragraph()
        p_name.alignment = PP_ALIGN.CENTER
        p_name.text = f"\n{stitle}"
        p_name.font.size = Pt(10)
        p_name.font.bold = True
        p_name.font.color.rgb = C_WHITE

        p_desc = tf_s.add_paragraph()
        p_desc.alignment = PP_ALIGN.CENTER
        p_desc.text = f"\n{sdesc}"
        p_desc.font.size = Pt(8.5)
        p_desc.font.color.rgb = C_MUTED

        if i < len(pipeline_8) - 1:
            arr_x = cx + p8_w + p8_gap
            add_arrow_pill(s3, arr_x, p8_top + Inches(1.3), p8_arr, Inches(0.2), C_BORDER_ACCENT)

    # Bottom Practical Summary Pipeline Flow
    # REPORTS → PROCESS → EXTRACT → RESOLVE → FUSE → GRAPH → QUERY → EVIDENCE
    b_flow = add_card(s3, Inches(0.9), Inches(5.35), Inches(11.533), Inches(1.4), C_CARD_OVERLAY, C_BORDER_ACCENT)
    tf_bf = b_flow.text_frame
    tf_bf.margin_left = Inches(0.3)
    tf_bf.margin_top = Inches(0.18)

    p_bfh = tf_bf.paragraphs[0]
    p_bfh.text = "CONTINUOUS REASONING FLOW (ZERO HALLUCINATIONS)"
    p_bfh.font.bold = True
    p_bfh.font.size = Pt(11)
    p_bfh.font.color.rgb = C_BORDER_ACCENT
    p_bfh.font.name = "Consolas"

    p_bfd = tf_bf.add_paragraph()
    p_bfd.text = "Every extracted entity, relationship, and GraphRAG answer links directly to page-numbered source evidence. Contradictory reports are flagged autonomously for analyst confirmation."
    p_bfd.font.size = Pt(11)
    p_bfd.font.color.rgb = C_OFF_WHITE

    # =========================================================================
    # SLIDE 4 — HOW TRINETRA WORKS (FOUR CONNECTED STEPS)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_solid_background(s4)
    apply_slide_transition(s4, "wipe", "r")
    add_header(s4, "Four steps to connect facts from reports", "HOW TRINETRA WORKS", 4)

    # Subtitle statement
    st4 = s4.shapes.add_textbox(Inches(0.9), Inches(1.45), Inches(11.5), Inches(0.45))
    tf_st4 = st4.text_frame
    p_st4 = tf_st4.paragraphs[0]
    p_st4.text = "“Autonomous 4-stage pipeline that unifies multi-source intelligence reports into verified facts.”"
    p_st4.font.size = Pt(14)
    p_st4.font.italic = True
    p_st4.font.color.rgb = C_GOLD_LIGHT

    # 4 Practical Process Cards connected by prominent chevron / flow arrows
    step_data = [
        ("01", "ADD REPORTS", "Upload several PDF reports.", "Batch multi-format ingestion:\n• Intelligence summaries\n• Field patrol logs\n• Signals intercepts & maps"),
        ("02", "FIND FACTS", "Find people, groups, events,\nequipment, places and links.", "Autonomous NER extraction:\n• Zero-shot entity recognition\n• Spatio-temporal anchoring\n• Subject-Predicate-Object triples"),
        ("03", "MATCH NAMES", "Vehicle 1 / Equipment 1 /\nTeam A / Event 1  →  Match", "Entity Resolution Engine:\n• Surface alias clustering\n• Phonetic & semantic matching\n• Cross-source entity linking"),
        ("04", "COMBINE", "Combine matching facts and\nkeep links to their sources.", "Knowledge Fusion & Provenance:\n• Merges into unified node\n• Flags contradictory dates/coords\n• 100% verifiable page citations")
    ]

    card_w4 = Inches(2.45)
    card_h4 = Inches(3.4)
    arr_w4 = Inches(0.42)
    gap4 = Inches(0.12)
    start_x4 = Inches(0.9)
    top_y4 = Inches(2.1)

    for i, (snum, stitle, ssub, sbody) in enumerate(step_data):
        cx = start_x4 + i * (card_w4 + arr_w4 + gap4 * 2)
        sc = add_card(s4, cx, top_y4, card_w4, card_h4, C_CARD_BASE, C_BORDER_ACCENT if i == 3 else C_BORDER_SUBTLE)
        tf_sc = sc.text_frame
        tf_sc.margin_left = Inches(0.2)
        tf_sc.margin_right = Inches(0.2)
        tf_sc.margin_top = Inches(0.22)

        p1 = tf_sc.paragraphs[0]
        p1.text = f"{snum} //"
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = C_GOLD
        p1.font.name = "Consolas"

        p2 = tf_sc.add_paragraph()
        p2.text = stitle
        p2.font.bold = True
        p2.font.size = Pt(14)
        p2.font.color.rgb = C_WHITE

        p3 = tf_sc.add_paragraph()
        p3.text = f"\n{ssub}"
        p3.font.bold = True
        p3.font.size = Pt(10.5)
        p3.font.color.rgb = C_BORDER_ACCENT

        p4 = tf_sc.add_paragraph()
        p4.text = f"\n{sbody}"
        p4.font.size = Pt(9.5)
        p4.font.color.rgb = C_MUTED

        if i < len(step_data) - 1:
            arr_x = cx + card_w4 + gap4
            add_arrow_pill(s4, arr_x, top_y4 + Inches(1.5), arr_w4, Inches(0.3), C_BORDER_ACCENT)

    # Bottom Practical Flow Callout
    bot4 = add_card(s4, Inches(0.9), Inches(5.8), Inches(11.533), Inches(1.05), C_CARD_DARK, C_BORDER_SUBTLE)
    tf_b4 = bot4.text_frame
    tf_b4.margin_left = Inches(0.3)
    tf_b4.margin_top = Inches(0.18)
    pb4 = tf_b4.paragraphs[0]
    pb4.text = "TACTICAL EXECUTION PRINCIPLE:"
    pb4.font.bold = True
    pb4.font.size = Pt(10)
    pb4.font.color.rgb = C_GOLD
    pb4.font.name = "Consolas"

    pb4_2 = tf_b4.add_paragraph()
    pb4_2.text = "TRINETRA automates the entire ingestion-to-graph pipeline in seconds, eliminating manual correlation bottlenecks."
    pb4_2.font.size = Pt(11)
    pb4_2.font.color.rgb = C_OFF_WHITE

    # =========================================================================
    # SLIDE 5 — FROM TEXT TO CONNECTED KNOWLEDGE (GRAPH DIAGRAM WITH ARROWS)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_solid_background(s5)
    apply_slide_transition(s5, "wipe", "r")
    add_header(s5, "Entities become a source-grounded graph", "FROM TEXT TO CONNECTED KNOWLEDGE", 5)

    # Core Rule Banner (ENTITY → RELATIONSHIP → ENTITY)
    rule_bar = add_card(s5, Inches(0.9), Inches(1.4), Inches(11.533), Inches(0.52), C_CARD_DARK, C_BORDER_ACCENT)
    tf_rb = rule_bar.text_frame
    tf_rb.vertical_anchor = MSO_ANCHOR.MIDDLE
    prb = tf_rb.paragraphs[0]
    prb.alignment = PP_ALIGN.CENTER
    prb.text = "SEMANTIC FOUNDATION:   [ ENTITY ]   ──────▶   ( RELATIONSHIP )   ──────▶   [ ENTITY ]"
    prb.font.bold = True
    prb.font.size = Pt(11)
    prb.font.color.rgb = C_BORDER_ACCENT
    prb.font.name = "Consolas"

    # Left: Practical Graphical Knowledge Graph Diagram
    diag_box = add_card(s5, Inches(0.9), Inches(2.15), Inches(6.8), Inches(4.7), C_CARD_BASE, C_BORDER_SUBTLE)
    tf_db = diag_box.text_frame
    tf_db.margin_left = Inches(0.25)
    tf_db.margin_top = Inches(0.2)
    pdb = tf_db.paragraphs[0]
    pdb.text = "SYNTHESIZED KNOWLEDGE GRAPH VISUALIZATION"
    pdb.font.bold = True
    pdb.font.size = Pt(11)
    pdb.font.color.rgb = C_GOLD
    pdb.font.name = "Consolas"

    # Draw Practical Node Cards inside the Diagram Box
    # Node 1: Vehicle A
    n_v = add_card(s5, Inches(1.3), Inches(2.8), Inches(2.2), Inches(0.9), RGBColor(35, 58, 40), C_BORDER_ACCENT)
    tf_v = n_v.text_frame
    tf_v.vertical_anchor = MSO_ANCHOR.MIDDLE
    pv = tf_v.paragraphs[0]
    pv.alignment = PP_ALIGN.CENTER
    pv.text = "Enemy Vehicle A\n[EQUIPMENT]"
    pv.font.bold = True
    pv.font.size = Pt(11)
    pv.font.color.rgb = C_WHITE

    # Horizontal Arrow from Vehicle A to Weapon X with label 'equipped with'
    add_relation_arrow(s5, Inches(3.6), Inches(3.1), Inches(1.5), Inches(0.24), "equipped with", C_BORDER_ACCENT, C_GOLD)

    # Node 2: Weapon X
    n_w = add_card(s5, Inches(5.2), Inches(2.8), Inches(2.2), Inches(0.9), RGBColor(45, 42, 25), C_GOLD)
    tf_w = n_w.text_frame
    tf_v.vertical_anchor = MSO_ANCHOR.MIDDLE
    pw = tf_w.paragraphs[0]
    pw.alignment = PP_ALIGN.CENTER
    pw.text = "Weapon X\n[WEAPONRY]"
    pw.font.bold = True
    pw.font.size = Pt(11)
    pw.font.color.rgb = C_WHITE

    # Down Arrow from Vehicle A to Unit Alpha with label 'associated with'
    add_down_arrow(s5, Inches(2.15), Inches(3.8), Inches(0.3), Inches(0.7), C_BORDER_ACCENT)
    lbl_assoc = s5.shapes.add_textbox(Inches(2.5), Inches(3.9), Inches(1.8), Inches(0.35))
    tf_la = lbl_assoc.text_frame
    pla = tf_la.paragraphs[0]
    pla.text = "associated with"
    pla.font.size = Pt(9)
    pla.font.bold = True
    pla.font.color.rgb = C_GOLD
    pla.font.name = "Consolas"

    # Node 3: Unit Alpha
    n_u = add_card(s5, Inches(1.3), Inches(4.6), Inches(2.2), Inches(0.9), RGBColor(30, 48, 55), C_TACTICAL_CYAN)
    tf_u = n_u.text_frame
    tf_u.vertical_anchor = MSO_ANCHOR.MIDDLE
    pu = tf_u.paragraphs[0]
    pu.alignment = PP_ALIGN.CENTER
    pu.text = "Unit Alpha\n[ORGANIZATION]"
    pu.font.bold = True
    pu.font.size = Pt(11)
    pu.font.color.rgb = C_WHITE

    # Horizontal Arrow from Unit Alpha to Incident Y with label 'mentioned in'
    add_relation_arrow(s5, Inches(3.6), Inches(4.9), Inches(1.5), Inches(0.24), "mentioned in", C_BORDER_ACCENT, C_GOLD)

    # Node 4: Incident Y
    n_y = add_card(s5, Inches(5.2), Inches(4.6), Inches(2.2), Inches(0.9), RGBColor(50, 25, 25), C_RED)
    tf_y = n_y.text_frame
    tf_y.vertical_anchor = MSO_ANCHOR.MIDDLE
    py = tf_y.paragraphs[0]
    py.alignment = PP_ALIGN.CENTER
    py.text = "Incident Y\n[EVENT]"
    py.font.bold = True
    py.font.size = Pt(11)
    py.font.color.rgb = C_WHITE

    # Bottom Discovery Callout in Diagram Box
    lbl_disc = s5.shapes.add_textbox(Inches(1.2), Inches(5.75), Inches(6.2), Inches(0.8))
    tf_ld = lbl_disc.text_frame
    pld = tf_ld.paragraphs[0]
    pld.text = "✓ Operational Discovery: Autonomous link established between Weapon X and Incident Y via common node Enemy Vehicle A."
    pld.font.size = Pt(10)
    pld.font.bold = True
    pld.font.color.rgb = C_BORDER_ACCENT

    # Right: Narrative & Source Grounding Principles
    right_box = add_card(s5, Inches(8.0), Inches(2.15), Inches(4.433), Inches(4.7), C_CARD_OVERLAY, C_BORDER_SUBTLE)
    tf_rb2 = right_box.text_frame
    tf_rb2.margin_left = Inches(0.3)
    tf_rb2.margin_top = Inches(0.25)
    tf_rb2.margin_right = Inches(0.25)

    prb2_h = tf_rb2.paragraphs[0]
    prb2_h.text = "SOURCE-GROUNDED TRACEABILITY"
    prb2_h.font.bold = True
    prb2_h.font.size = Pt(12)
    prb2_h.font.color.rgb = C_BORDER_ACCENT
    prb2_h.font.name = "Consolas"

    points5 = [
        ("Connected Through Evidence", "Every relationship in the graph is strictly supported by source documents. No speculative links."),
        ("Provenance Preservation", "Each edge stores document ID, page number, and source sentence offset for instant analyst verification."),
        ("Multi-Hop Reasoning", "GraphRAG traces 2-hop and 3-hop connections that analysts cannot spot across multiple distinct PDFs."),
        ("Discrepancy Auditing", "If Report 01 and Report 03 report conflicting coordinates, a discrepancy badge is flagged autonomously.")
    ]

    for ptitle, pdesc in points5:
        p_pt = tf_rb2.add_paragraph()
        p_pt.text = f"\n▸  {ptitle}"
        p_pt.font.bold = True
        p_pt.font.size = Pt(11.5)
        p_pt.font.color.rgb = C_GOLD_LIGHT

        p_pd = tf_rb2.add_paragraph()
        p_pd.text = f"    {pdesc}"
        p_pd.font.size = Pt(10)
        p_pd.font.color.rgb = C_MUTED

    # =========================================================================
    # SLIDE 6 — AGENTIC AI WORKFLOW (SPECIALIZED AGENTS WITH ARROWS)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_solid_background(s6)
    apply_slide_transition(s6, "wipe", "r")
    add_header(s6, "Specialized agents collaborate across the evidence chain", "AGENTIC AI WORKFLOW", 6)

    # Subtitle statement
    st6 = s6.shapes.add_textbox(Inches(0.9), Inches(1.45), Inches(11.5), Inches(0.45))
    tf_st6 = st6.text_frame
    p_st6 = tf_st6.paragraphs[0]
    p_st6.text = "“Specialized agents transform unstructured reports into structured, connected knowledge.”"
    p_st6.font.size = Pt(14)
    p_st6.font.italic = True
    p_st6.font.color.rgb = C_BORDER_ACCENT

    # 6 Agents + Output Terminal Card (Pipeline with Practical Arrows)
    agents_chain = [
        ("01", "DOCUMENT\nAGENT", "Ingests PDF, DOCX,\nTXT & map imagery"),
        ("02", "EXTRACTION\nAGENT", "Zero-shot entity\n& triple recognition"),
        ("03", "ENTITY RES\nAGENT", "Harmonizes aliases\n& clusters duplicates"),
        ("04", "KNOWLEDGE\nFUSION AGENT", "Constructs graph &\naudits discrepancies"),
        ("05", "KNOWLEDGE\nGRAPH", "Decentralized RDF\nnetwork topology"),
        ("06", "QUERY\nAGENT", "GraphRAG multi-hop\nreasoning engine"),
        ("OUT", "ANSWER +\nEVIDENCE", "Grounded answer with\nsource citations")
    ]

    aw6 = Inches(1.36)
    arr_w6 = Inches(0.24)
    gap6 = Inches(0.04)
    ay6 = Inches(2.25)
    start_x6 = Inches(0.9)

    for i, (snum, aname, adesc) in enumerate(agents_chain):
        cx = start_x6 + i * (aw6 + arr_w6 + gap6 * 2)
        is_end = (i == 6)
        is_graph = (i == 4)
        bg = RGBColor(38, 62, 42) if is_graph else (RGBColor(48, 56, 32) if is_end else C_CARD_BASE)
        brd = C_BORDER_ACCENT if is_end else (C_GOLD if is_graph else C_BORDER_SUBTLE)

        ac = add_card(s6, cx, ay6, aw6, Inches(3.0), bg, brd)
        tf_a = ac.text_frame
        tf_a.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf_a.margin_left = tf_a.margin_right = Inches(0.06)

        p_idx = tf_a.paragraphs[0]
        p_idx.alignment = PP_ALIGN.CENTER
        p_idx.text = f"{snum}"
        p_idx.font.size = Pt(11)
        p_idx.font.bold = True
        p_idx.font.color.rgb = C_GOLD
        p_idx.font.name = "Consolas"

        p_name = tf_a.add_paragraph()
        p_name.alignment = PP_ALIGN.CENTER
        p_name.text = f"\n{aname}"
        p_name.font.size = Pt(10)
        p_name.font.bold = True
        p_name.font.color.rgb = C_WHITE

        p_desc = tf_a.add_paragraph()
        p_desc.alignment = PP_ALIGN.CENTER
        p_desc.text = f"\n{adesc}"
        p_desc.font.size = Pt(8.5)
        p_desc.font.color.rgb = C_MUTED

        if i < len(agents_chain) - 1:
            arr_x = cx + aw6 + gap6
            add_arrow_pill(s6, arr_x, ay6 + Inches(1.35), arr_w6, Inches(0.2), C_BORDER_ACCENT)

    # Architecture Assurance Footer
    f6_box = add_card(s6, Inches(0.9), Inches(5.6), Inches(11.533), Inches(1.2), C_CARD_OVERLAY, C_BORDER_SUBTLE)
    tf_f6 = f6_box.text_frame
    tf_f6.margin_left = Inches(0.3)
    tf_f6.margin_top = Inches(0.18)
    pf6_1 = tf_f6.paragraphs[0]
    pf6_1.text = "DECENTRALIZED AGENTIC COLLABORATION PRINCIPLE"
    pf6_1.font.bold = True
    pf6_1.font.size = Pt(11)
    pf6_1.font.color.rgb = C_BORDER_ACCENT
    pf6_1.font.name = "Consolas"

    pf6_2 = tf_f6.add_paragraph()
    pf6_2.text = "Specialized autonomous agents communicate through explicit semantic protocols. Each agent executes a deterministic intelligence task, ensuring 100% auditability and eliminating single points of failure."
    pf6_2.font.size = Pt(10.5)
    pf6_2.font.color.rgb = C_OFF_WHITE

    # =========================================================================
    # SLIDE 7 — THREE REPORTS, ONE CONNECTED VIEW (PRACTICAL DEMO ARROWS)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_solid_background(s7)
    apply_slide_transition(s7, "wipe", "r")
    add_header(s7, "Three reports, one connected view", "FICTIONAL / SYNTHETIC DEMO DATA · TRINETRA IN ACTION", 7)

    # Top Synthetic disclaimer banner
    badge7 = add_card(s7, Inches(0.9), Inches(1.4), Inches(11.533), Inches(0.4), C_CARD_DARK, C_GOLD)
    tf_b7 = badge7.text_frame
    tf_b7.vertical_anchor = MSO_ANCHOR.MIDDLE
    pb7 = tf_b7.paragraphs[0]
    pb7.alignment = PP_ALIGN.CENTER
    pb7.text = "FICTIONAL / SYNTHETIC DEMO DATA  •  NO REAL MILITARY LOCATIONS, UNITS OR TARGETING"
    pb7.font.size = Pt(10)
    pb7.font.bold = True
    pb7.font.color.rgb = C_GOLD_LIGHT
    pb7.font.name = "Consolas"

    # 3 Input Report Cards at Top
    r_w7 = Inches(3.64)
    r_h7 = Inches(1.6)
    r_gap7 = Inches(0.3)
    r_top7 = Inches(2.05)

    reports_data = [
        ("REPORT 01 (PATROL LOG)", "Enemy Vehicle A equipped with Weapon X", "📄 Source: Sector Bravo Recon Brief\n• Entity: Enemy Vehicle A\n• Mount: Weapon X armament"),
        ("REPORT 02 (SIGNALS INTERCEPT)", "Enemy Vehicle A linked to Unit Alpha", "📄 Source: Communications Intercept 09\n• Entity: Enemy Vehicle A\n• Affiliation: Unit Alpha command"),
        ("REPORT 03 (SURVEILLANCE)", "Unit Alpha mentioned in Incident Y", "📄 Source: Perimeter Camera Log 14\n• Entity: Unit Alpha\n• Context: Active at Incident Y")
    ]

    for i, (rtitle, rfact, rmeta) in enumerate(reports_data):
        rx = Inches(0.9) + i * (r_w7 + r_gap7)
        rc = add_card(s7, rx, r_top7, r_w7, r_h7, C_CARD_BASE, C_BORDER_SUBTLE)
        tf_rc = rc.text_frame
        tf_rc.margin_left = Inches(0.2)
        tf_rc.margin_top = Inches(0.18)

        pr1 = tf_rc.paragraphs[0]
        pr1.text = rtitle
        pr1.font.bold = True
        pr1.font.size = Pt(10)
        pr1.font.color.rgb = C_BORDER_ACCENT
        pr1.font.name = "Consolas"

        pr2 = tf_rc.add_paragraph()
        pr2.text = rfact
        pr2.font.bold = True
        pr2.font.size = Pt(11.5)
        pr2.font.color.rgb = C_WHITE

        pr3 = tf_rc.add_paragraph()
        pr3.text = f"\n{rmeta}"
        pr3.font.size = Pt(9)
        pr3.font.color.rgb = C_MUTED

    # Practical Downward Convergence Arrows from 3 Reports into Fused View
    add_down_arrow(s7, Inches(2.6), Inches(3.75), Inches(0.3), Inches(0.35), C_BORDER_ACCENT)
    add_down_arrow(s7, Inches(6.55), Inches(3.75), Inches(0.3), Inches(0.35), C_BORDER_ACCENT)
    add_down_arrow(s7, Inches(10.5), Inches(3.75), Inches(0.3), Inches(0.35), C_BORDER_ACCENT)

    # Bottom Fused Intelligence View Container
    fused_box7 = add_card(s7, Inches(0.9), Inches(4.2), Inches(11.533), Inches(2.65), C_CARD_OVERLAY, C_BORDER_ACCENT)
    tf_f7 = fused_box7.text_frame
    tf_f7.margin_left = Inches(0.3)
    tf_f7.margin_top = Inches(0.2)

    pf7_h = tf_f7.paragraphs[0]
    pf7_h.text = "TRINETRA FUSED INTELLIGENCE SYNTHESIS"
    pf7_h.font.bold = True
    pf7_h.font.size = Pt(12)
    pf7_h.font.color.rgb = C_BORDER_ACCENT
    pf7_h.font.name = "Consolas"

    # Practical Connected Flow Badge
    pfc = tf_f7.add_paragraph()
    pfc.text = "\nUnified Knowledge Trajectory:"
    pfc.font.size = Pt(11)
    pfc.font.color.rgb = C_MUTED

    pf_flow = tf_f7.add_paragraph()
    pf_flow.text = "Vehicle A   ──▶   Weapon X   •   Unit Alpha   •   Incident Y"
    pf_flow.font.bold = True
    pf_flow.font.size = Pt(15)
    pf_flow.font.color.rgb = C_GOLD
    pf_flow.font.name = "Consolas"

    pf_disc = tf_f7.add_paragraph()
    pf_disc.text = "\n• Operational Insight: Automated fusion reveals that Weapon X is linked to Incident Y through common entity Enemy Vehicle A."
    pf_disc.font.size = Pt(11)
    pf_disc.font.color.rgb = C_OFF_WHITE

    pf_foot = tf_f7.add_paragraph()
    pf_foot.text = "• Note: Fictional vehicle and aircraft silhouettes remain secondary to the verifiable evidence graph."
    pf_foot.font.size = Pt(9.5)
    pf_foot.font.italic = True
    pf_foot.font.color.rgb = C_DIM

    # =========================================================================
    # SLIDE 8 — USER EXPERIENCE (ONE WORKSPACE FOR THE ANALYST)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_solid_background(s8)
    apply_slide_transition(s8, "wipe", "r")
    add_header(s8, "One workspace for the analyst", "SIMPLE USER EXPERIENCE", 8)

    # 3 Feature Section Cards on Left
    s8_left_x = Inches(0.9)
    s8_left_w = Inches(4.5)
    s8_sections = [
        ("01 — DASHBOARD", "Knowledge Graph + Key Statistics", "Processing status, entity / relationship counts, and autonomous conflict indicator at a glance.", C_BORDER_ACCENT),
        ("02 — SOURCES", "Upload & Manage Multiple Reports", "Drag-and-drop ingestion of multiple PDF reports with interactive split-view text inspector.", C_GOLD),
        ("03 — ASK TRINETRA", "Source-Grounded Natural Language QA", "Ask tactical questions and receive answers strictly supported by source citations and page numbers.", C_TACTICAL_CYAN)
    ]

    sec_h8 = Inches(1.45)
    sec_gap8 = Inches(0.25)
    top_y8 = Inches(1.8)

    for i, (title_s, sub_s, desc_s, col_s) in enumerate(s8_sections):
        sc = add_card(s8, s8_left_x, top_y8 + i * (sec_h8 + sec_gap8), s8_left_w, sec_h8, C_CARD_BASE, col_s)
        tf_sc = sc.text_frame
        tf_sc.margin_left = Inches(0.22)
        tf_sc.margin_top = Inches(0.18)

        p1 = tf_sc.paragraphs[0]
        p1.text = title_s
        p1.font.bold = True
        p1.font.size = Pt(12)
        p1.font.color.rgb = col_s
        p1.font.name = "Consolas"

        p2 = tf_sc.add_paragraph()
        p2.text = sub_s
        p2.font.bold = True
        p2.font.size = Pt(11)
        p2.font.color.rgb = C_WHITE

        p3 = tf_sc.add_paragraph()
        p3.text = desc_s
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = C_MUTED

    # Right: UI Mockup Preview
    mockup_x = Inches(5.7)
    mockup_w = Inches(6.733)
    mockup_h = Inches(4.85)

    if os.path.exists(IMG_UI):
        s8.shapes.add_picture(IMG_UI, mockup_x, top_y8, mockup_w, mockup_h)
        mb = s8.shapes.add_shape(MSO_SHAPE.RECTANGLE, mockup_x, top_y8, mockup_w, mockup_h)
        mb.fill.background()
        mb.line.color.rgb = C_BORDER_ACCENT
        mb.line.width = Pt(1.5)
    else:
        # Placeholder tactical card
        add_card(s8, mockup_x, top_y8, mockup_w, mockup_h, C_CARD_OVERLAY, C_BORDER_ACCENT)

    # Sub-caption
    cap8 = s8.shapes.add_textbox(mockup_x, Inches(6.75), mockup_w, Inches(0.35))
    tf_c8 = cap8.text_frame
    pc8 = tf_c8.paragraphs[0]
    pc8.alignment = PP_ALIGN.RIGHT
    pc8.text = "FICTIONAL / SYNTHETIC UI MOCKUP  •  PS-05 ANALYST CONSOLE"
    pc8.font.size = Pt(9.5)
    pc8.font.color.rgb = C_DIM
    pc8.font.name = "Consolas"

    # =========================================================================
    # SLIDE 9 — LIVE DEMO (END TO END WITH PRACTICAL ARROWS)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_solid_background(s9)
    apply_slide_transition(s9, "wipe", "r")
    add_header(s9, "LIVE DEMO — END TO END", "FICTIONAL / SYNTHETIC DEMO DATA", 9)

    # Practical 8-Step Interactive Process Flow Bar
    flow_steps = [
        "1. UPLOAD",
        "2. PROCESS",
        "3. EXTRACT",
        "4. RESOLVE",
        "5. FUSE",
        "6. GRAPH",
        "7. ASK",
        "8. ANSWER"
    ]

    fbar_y = Inches(1.4)
    fbar_h = Inches(0.55)
    f_step_w = Inches(1.15)
    f_arr_w9 = Inches(0.2)
    f_gap9 = Inches(0.04)
    f_start_x9 = Inches(0.9)

    # Container card for flow bar
    add_card(s9, Inches(0.9), fbar_y, Inches(11.533), fbar_h, C_CARD_DARK, C_BORDER_SUBTLE)

    for i, sname in enumerate(flow_steps):
        sx = f_start_x9 + Inches(0.15) + i * (f_step_w + f_arr_w9 + f_gap9 * 2)
        sbox = add_card(s9, sx, fbar_y + Inches(0.08), f_step_w, Inches(0.38), C_CARD_BASE, C_BORDER_ACCENT if i == 7 else C_BORDER_SUBTLE)
        tf_sb = sbox.text_frame
        tf_sb.vertical_anchor = MSO_ANCHOR.MIDDLE
        psb = tf_sb.paragraphs[0]
        psb.alignment = PP_ALIGN.CENTER
        psb.text = sname
        psb.font.bold = True
        psb.font.size = Pt(9)
        psb.font.color.rgb = C_BORDER_ACCENT if i == 7 else C_WHITE
        psb.font.name = "Consolas"

        if i < len(flow_steps) - 1:
            ax9 = sx + f_step_w + f_gap9
            add_arrow_pill(s9, ax9, fbar_y + Inches(0.17), f_arr_w9, Inches(0.18), C_BORDER_ACCENT)

    # Example Query Box
    q_card = add_card(s9, Inches(0.9), Inches(2.15), Inches(11.533), Inches(1.1), C_CARD_OVERLAY, C_GOLD)
    tf_q = q_card.text_frame
    tf_q.margin_left = Inches(0.3)
    tf_q.margin_top = Inches(0.15)

    pq_lbl = tf_q.paragraphs[0]
    pq_lbl.text = "EXAMPLE ANALYST QUERY:"
    pq_lbl.font.bold = True
    pq_lbl.font.size = Pt(10)
    pq_lbl.font.color.rgb = C_GOLD
    pq_lbl.font.name = "Consolas"

    pq_text = tf_q.add_paragraph()
    pq_text.text = "“What information is available about Enemy Vehicle A?”"
    pq_text.font.bold = True
    pq_text.font.size = Pt(16)
    pq_text.font.color.rgb = C_WHITE

    # Answer Breakdown Panel
    ans_card = add_card(s9, Inches(0.9), Inches(3.45), Inches(11.533), Inches(3.55), C_CARD_BASE, C_BORDER_ACCENT)
    tf_ans = ans_card.text_frame
    tf_ans.margin_left = Inches(0.35)
    tf_ans.margin_top = Inches(0.2)

    pa_head = tf_ans.paragraphs[0]
    pa_head.text = "TRINETRA SYNTHESIS & AUDIT RESULT  [VERIFIED FICTIONAL EVIDENCE]"
    pa_head.font.bold = True
    pa_head.font.size = Pt(11)
    pa_head.font.color.rgb = C_BORDER_ACCENT
    pa_head.font.name = "Consolas"

    pa1 = tf_ans.add_paragraph()
    pa1.text = "\n• Expected Result: Combined multi-source information, related entities, and supporting report/page references."
    pa1.font.size = Pt(11.5)
    pa1.font.color.rgb = C_WHITE

    pa2 = tf_ans.add_paragraph()
    pa2.text = "• Related Entities: Weapon X (Equipment)  •  Unit Alpha (Organizations)  •  Incident Y (Events)"
    pa2.font.size = Pt(11.5)
    pa2.font.bold = True
    pa2.font.color.rgb = C_GOLD

    pa3 = tf_ans.add_paragraph()
    pa3.text = "\n• Evidence Citations:\n    - Fictional Report 01, p. 2: 'Enemy Vehicle A observed with Weapon X mounts.'\n    - Fictional Report 03, p. 1: 'Unit Alpha presence confirmed at Incident Y.'"
    pa3.font.size = Pt(10)
    pa3.font.color.rgb = C_MUTED
    pa3.font.name = "Consolas"

    pa4 = tf_ans.add_paragraph()
    pa4.text = "\n• Guardrail Enforcement: Unsupported query  ──▶  INSUFFICIENT SOURCE EVIDENCE (Zero Hallucinations Guarantee)"
    pa4.font.bold = True
    pa4.font.size = Pt(11)
    pa4.font.color.rgb = C_RED
    pa4.font.name = "Consolas"

    # =========================================================================
    # SLIDE 10 — CLOSING / THANK YOU (PRACTICAL MOTTO FLOW)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    apply_slide_transition(s10, "fade")

    if os.path.exists(IMG_TRICOLOUR_BG):
        s10.shapes.add_picture(IMG_TRICOLOUR_BG, 0, 0, Inches(13.333), Inches(7.5))
        overlay10 = s10.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        overlay10.fill.solid()
        overlay10.fill.fore_color.rgb = C_BG_MILITARY
        overlay10.line.fill.background()
    else:
        set_solid_background(s10)

    # Center Hero Card
    c_card = add_card(s10, Inches(2.2), Inches(1.1), Inches(8.933), Inches(5.3), C_CARD_BASE, C_GOLD)
    tf_c10 = c_card.text_frame
    tf_c10.vertical_anchor = MSO_ANCHOR.MIDDLE

    p_em = tf_c10.paragraphs[0]
    p_em.alignment = PP_ALIGN.CENTER
    p_em.text = "TRINETRA"
    p_em.font.size = Pt(14)
    p_em.font.bold = True
    p_em.font.color.rgb = C_BORDER_ACCENT
    p_em.font.name = "Consolas"

    p_ty = tf_c10.add_paragraph()
    p_ty.alignment = PP_ALIGN.CENTER
    p_ty.text = "THANK YOU"
    p_ty.font.size = Pt(44)
    p_ty.font.bold = True
    p_ty.font.color.rgb = C_WHITE
    p_ty.font.name = "Arial"

    p_tg = tf_c10.add_paragraph()
    p_tg.alignment = PP_ALIGN.CENTER
    p_tg.text = "“From Fragmented Information to Strategic Insight.”"
    p_tg.font.size = Pt(16)
    p_tg.font.italic = True
    p_tg.font.color.rgb = C_GOLD
    p_tg.font.name = "Georgia"

    # Practical Flow Motto: Connect → Fuse → Discover → Query
    motto_steps = ["Connect", "Fuse", "Discover", "Query"]
    m_w = Inches(1.4)
    m_arr = Inches(0.3)
    m_gap = Inches(0.08)
    m_start_x = Inches(3.45)
    m_y = Inches(4.5)

    for i, mword in enumerate(motto_steps):
        mx = m_start_x + i * (m_w + m_arr + m_gap * 2)
        mbx = add_card(s10, mx, m_y, m_w, Inches(0.48), C_CARD_DARK, C_BORDER_ACCENT)
        tf_m = mbx.text_frame
        tf_m.vertical_anchor = MSO_ANCHOR.MIDDLE
        pm = tf_m.paragraphs[0]
        pm.alignment = PP_ALIGN.CENTER
        pm.text = mword
        pm.font.bold = True
        pm.font.size = Pt(11)
        pm.font.color.rgb = C_WHITE
        pm.font.name = "Consolas"

        if i < len(motto_steps) - 1:
            arr_mx = mx + m_w + m_gap
            add_arrow_pill(s10, arr_mx, m_y + Inches(0.14), m_arr, Inches(0.2), C_BORDER_ACCENT)

    p_jh = tf_c10.add_paragraph()
    p_jh.alignment = PP_ALIGN.CENTER
    p_jh.text = "\nJAI HIND 🇮🇳"
    p_jh.font.size = Pt(24)
    p_jh.font.bold = True
    p_jh.font.color.rgb = C_GOLD
    p_jh.font.name = "Arial"

    # Save to PowerPoint files
    out_workspace = r"d:\TRINETRA\TRINETRA_Hackathon_Presentation.pptx"
    out_frontend = r"d:\TRINETRA\frontend\TRINETRA_Hackathon_Presentation.pptx"
    out_downloads = os.path.expanduser(r"~\Downloads\TRINETRA_Hackathon_Presentation.pptx")

    prs.save(out_workspace)
    prs.save(out_frontend)
    shutil.copy2(out_workspace, out_downloads)

    print(f"✓ Saved Presentation to Workspace: {out_workspace}")
    print(f"✓ Saved Presentation to Frontend:  {out_frontend}")
    print(f"✓ Saved Presentation to Downloads: {out_downloads}")

if __name__ == "__main__":
    build_presentation()
