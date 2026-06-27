import fitz
import re
from datetime import datetime

# ── Color Palette ─────────────────────────────────────────────────────────────
WHITE        = (1.0,  1.0,  1.0)
BLACK        = (0.1,  0.1,  0.1)
NAVY         = (0.10, 0.23, 0.42)   # #1a3a6b - primary brand
NAVY_LIGHT   = (0.18, 0.35, 0.58)   # subheadings / meta boxes
GREY_BG      = (0.95, 0.96, 0.97)   # alternating table rows
GREY_LINE    = (0.75, 0.78, 0.82)   # table borders
GREY_TEXT    = (0.35, 0.37, 0.40)   # secondary text
DARK_TEXT    = (0.10, 0.10, 0.10)   # body text
GREEN        = (0.07, 0.47, 0.24)   # positive / strong fit
AMBER        = (0.75, 0.45, 0.00)   # medium fit / warning
RED          = (0.70, 0.10, 0.10)   # risk / disqualified
YELLOW_BG    = (1.0,  0.97, 0.88)   # light amber background
COVER_BG     = (0.10, 0.23, 0.42)   # navy cover background
TEAL         = (0.04, 0.52, 0.52)   # accent for enrichment section

PAGE_W = 595
PAGE_H = 842
MARGIN = 50
CONTENT_W = PAGE_W - MARGIN * 2


# ── Core Helpers ──────────────────────────────────────────────────────────────

def _new_page(doc, white=True):
    page = doc.new_page(width=PAGE_W, height=PAGE_H)
    if white:
        page.draw_rect(fitz.Rect(0, 0, PAGE_W, PAGE_H), color=WHITE, fill=WHITE)
    else:
        page.draw_rect(fitz.Rect(0, 0, PAGE_W, PAGE_H), color=COVER_BG, fill=COVER_BG)
    return page


def _text(page, text, x, y, size=10, color=DARK_TEXT, bold=False):
    fontname = "hebo" if bold else "helv"
    try:
        page.insert_text((x, y), str(text), fontname=fontname, fontsize=size, color=color)
    except Exception:
        pass


def _wrap_text(page, text, x, y, max_width, size=10, color=DARK_TEXT,
               line_height=15, max_y=800):
    """Word-wrap text within max_width. Returns final y."""
    words = str(text).split()
    line  = ""
    cur_y = y
    for word in words:
        test = (line + " " + word).strip()
        if len(test) * size * 0.52 > max_width and line:
            if cur_y < max_y:
                try:
                    page.insert_text((x, cur_y), line,
                                     fontname="helv", fontsize=size, color=color)
                except Exception:
                    pass
            cur_y += line_height
            line = word
        else:
            line = test
    if line and cur_y < max_y:
        try:
            page.insert_text((x, cur_y), line,
                             fontname="helv", fontsize=size, color=color)
        except Exception:
            pass
    return cur_y + line_height


def _divider(page, y, color=NAVY, width=1.0):
    page.draw_line((MARGIN, y), (PAGE_W - MARGIN, y), color=color, width=width)


def _thin_divider(page, y):
    page.draw_line((MARGIN, y), (PAGE_W - MARGIN, y), color=GREY_LINE, width=0.5)


def _section_title(page, title, y, color=NAVY):
    """Navy section title with underline rule."""
    _text(page, title.upper(), MARGIN, y, size=12, color=color, bold=True)
    y += 6
    _divider(page, y, color=color, width=1.5)
    return y + 14


def _footer(page, page_num, total):
    _thin_divider(page, PAGE_H - 35)
    _text(page, "ProcureAI  |  Customer Discovery Report  |  Confidential",
          MARGIN, PAGE_H - 20, size=8, color=GREY_TEXT)
    _text(page, f"Page {page_num} of {total}",
          PAGE_W - MARGIN - 60, PAGE_H - 20, size=8, color=GREY_TEXT)
    _text(page, datetime.now().strftime("%B %d, %Y"),
          PAGE_W // 2 - 35, PAGE_H - 20, size=8, color=GREY_TEXT)


def _header_bar(page, title, subtitle=""):
    """Top navy bar for all inner pages."""
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, 58), color=NAVY, fill=NAVY)
    _text(page, "ProcureAI", MARGIN, 22, size=10, color=WHITE, bold=True)
    _text(page, title, MARGIN, 42, size=15, color=WHITE, bold=True)
    if subtitle:
        _text(page, subtitle,
              PAGE_W - MARGIN - len(subtitle) * 5.5, 42, size=9, color=GREY_LINE)
    return 78


def _clean(text):
    """Strip markdown, box-drawing chars, and non-latin glyphs."""
    if not text:
        return "N/A"
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*',     r'\1', text)
    text = re.sub(r'#{1,6}\s?',     '',    text)
    text = re.sub(r'`(.*?)`',       r'\1', text)
    # strip box-drawing / special unicode that helv can't render
    text = re.sub(r'[^\x00-\xFF]', '', text)
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text.strip()


# ── Table Helpers ─────────────────────────────────────────────────────────────

def _parse_markdown_table(text):
    lines       = text.split('\n')
    table_lines = []
    in_table    = False
    for line in lines:
        line = line.strip()
        if line.startswith('|') and '|' in line[1:]:
            in_table = True
            table_lines.append(line)
        elif in_table:
            break
    if len(table_lines) < 2:
        return None, None

    def parse_row(line):
        return [c.strip() for c in line.strip('|').split('|')]

    headers = parse_row(table_lines[0])
    rows = [parse_row(l) for l in table_lines[2:] if l.startswith('|')]
    return headers, rows


def _draw_table(page, headers, rows, x, y, max_y=800, col_widths=None):
    """Draw a bordered table. Returns final y."""
    if not headers:
        return y
    n_cols  = len(headers)
    if col_widths:
        # normalise to content width
        total = sum(col_widths)
        col_w_list = [CONTENT_W * w / total for w in col_widths]
    else:
        col_w_list = [CONTENT_W / n_cols] * n_cols

    row_h    = 18
    header_h = 22

    # Header background
    page.draw_rect(fitz.Rect(x, y, x + CONTENT_W, y + header_h),
                   color=NAVY, fill=NAVY)
    cx = x
    for i, h in enumerate(headers):
        _text(page, str(h)[:24], cx + 4, y + 14, size=8, color=WHITE, bold=True)
        cx += col_w_list[i]
    y += header_h

    # Data rows
    drawn_rows = 0
    for r_idx, row in enumerate(rows):
        if y + row_h > max_y:
            break
        bg = GREY_BG if r_idx % 2 == 0 else WHITE
        page.draw_rect(fitz.Rect(x, y, x + CONTENT_W, y + row_h), color=bg, fill=bg)
        cx = x
        for i, cell in enumerate(row[:n_cols]):
            _text(page, str(cell)[:30], cx + 4, y + 12, size=8, color=DARK_TEXT)
            cx += col_w_list[i]
        page.draw_line((x, y + row_h), (x + CONTENT_W, y + row_h),
                       color=GREY_LINE, width=0.3)
        y += row_h
        drawn_rows += 1

    # Outer border
    total_h = header_h + drawn_rows * row_h
    page.draw_rect(fitz.Rect(x, y - total_h, x + CONTENT_W, y),
                   color=GREY_LINE, width=0.8)
    # Column dividers
    cx = x
    for i in range(1, n_cols):
        cx += col_w_list[i - 1]
        page.draw_line((cx, y - total_h), (cx, y), color=GREY_LINE, width=0.3)

    return y + 10


def _render_agent_output(page, text, y, max_y=790):
    """
    Render agent text:
    - Markdown tables → proper bordered table
    - Numbered headings → navy bold
    - Bullet lines → bullet points
    - Plain lines → word-wrapped body text
    """
    text  = _clean(text)
    lines = text.split('\n')

    headers, rows = _parse_markdown_table(text)
    if headers and rows:
        y = _draw_table(page, headers, rows, MARGIN, y, max_y=max_y)
        y += 8

    for line in lines:
        line = line.strip()
        if not line:
            y += 4
            continue
        if line.startswith('|'):
            continue  # already rendered above

        if re.match(r'^[1-9]\.\s', line) or re.match(r'^\*\*.*\*\*$', line):
            heading = re.sub(r'^\d+\.\s*', '', line)
            heading = re.sub(r'\*\*(.*?)\*\*', r'\1', heading)
            y += 5
            if y > max_y:
                break
            _text(page, _clean(heading), MARGIN, y, size=10, color=NAVY, bold=True)
            y += 14
        elif line.startswith('##'):
            heading = line.lstrip('#').strip()
            y += 6
            if y > max_y:
                break
            _text(page, _clean(heading).upper(), MARGIN, y, size=9,
                  color=NAVY_LIGHT, bold=True)
            y += 13
        elif line.startswith('-') or line.startswith('*'):
            bullet = line.lstrip('-* ').strip()
            if y > max_y:
                break
            _text(page, chr(8226), MARGIN, y, size=10, color=NAVY, bold=True)
            y = _wrap_text(page, _clean(bullet), MARGIN + 14, y,
                           CONTENT_W - 14, size=9.5, color=DARK_TEXT,
                           line_height=14, max_y=max_y)
        else:
            if y > max_y:
                break
            y = _wrap_text(page, _clean(line), MARGIN, y, CONTENT_W,
                           size=9.5, color=DARK_TEXT, line_height=14, max_y=max_y)
        y += 2

    return y


def _stat_card(page, label, value, x, y, w=115, h=52, accent=NAVY):
    """Small KPI card with accent left bar."""
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=GREY_BG, fill=GREY_BG)
    page.draw_rect(fitz.Rect(x, y, x + w, y + h), color=GREY_LINE, width=0.6)
    page.draw_rect(fitz.Rect(x, y, x + 4, y + h), color=accent, fill=accent)
    _text(page, label, x + 10, y + 16, size=7.5, color=GREY_TEXT, bold=True)
    _text(page, str(value), x + 10, y + 36, size=13, color=accent, bold=True)


# ── PDF Entry Point ───────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    extracted_text = ""
    for page_number in range(len(pdf_document)):
        page = pdf_document[page_number]
        extracted_text += page.get_text()
    pdf_document.close()
    return extracted_text


def generate_pdf_report(results: dict, vendor_names: list) -> bytes:
    doc         = fitz.open()
    total_pages = 8

    # pull inputs if passed through results
    product  = _clean(results.get("product_description", "SaaS Product"))
    industry = _clean(results.get("target_industry", vendor_names[0] if vendor_names else "Industry"))
    location = _clean(results.get("target_location", "Target Location"))
    persona  = _clean(results.get("target_persona",  "Decision Maker"))
    size     = _clean(results.get("company_size",    "Target Size"))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — COVER  (Navy Background)
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=False)

    # Top white accent
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, 8), color=WHITE, fill=WHITE)

    # Logo box
    page.draw_rect(fitz.Rect(MARGIN, 110, MARGIN + 78, 172), color=WHITE, fill=WHITE)
    _text(page, "AI", MARGIN + 16, 158, size=32, color=NAVY, bold=True)

    # Title block
    _text(page, "ProcureAI",                    MARGIN, 210, size=38, color=WHITE, bold=True)
    _text(page, "Customer Discovery Report",     MARGIN, 248, size=17, color=GREY_LINE)
    page.draw_line((MARGIN, 268), (PAGE_W - MARGIN, 268), color=WHITE, width=0.8)

    # Meta info box
    page.draw_rect(fitz.Rect(MARGIN, 288, PAGE_W - MARGIN, 450),
                   color=NAVY_LIGHT, fill=NAVY_LIGHT)

    _text(page, "PRODUCT",        MARGIN + 18, 310, size=8,  color=GREY_LINE, bold=True)
    prod_short = product[:72] + "..." if len(product) > 72 else product
    _text(page, prod_short,       MARGIN + 18, 328, size=9,  color=WHITE)

    _text(page, "TARGET INDUSTRY",MARGIN + 18, 355, size=8,  color=GREY_LINE, bold=True)
    _text(page, industry,         MARGIN + 18, 372, size=10, color=WHITE)

    _text(page, "TARGET LOCATION",MARGIN + 18, 398, size=8,  color=GREY_LINE, bold=True)
    _text(page, location,         MARGIN + 18, 415, size=10, color=WHITE)

    _text(page, "DECISION MAKER", PAGE_W // 2 + 10, 355, size=8,  color=GREY_LINE, bold=True)
    _text(page, persona,          PAGE_W // 2 + 10, 372, size=10, color=WHITE)

    _text(page, "COMPANY SIZE",   PAGE_W // 2 + 10, 398, size=8,  color=GREY_LINE, bold=True)
    _text(page, size,             PAGE_W // 2 + 10, 415, size=10, color=WHITE)

    _text(page, "DATE GENERATED", MARGIN + 18, 436, size=8,  color=GREY_LINE, bold=True)
    _text(page, datetime.now().strftime("%B %d, %Y"), MARGIN + 130, 436, size=9, color=WHITE)

    _text(page,
          "Powered by LangGraph  |  LLaMA 3.1 8B Instant  |  Tavily  |  FastAPI  |  Groq",
          MARGIN, 478, size=8.5, color=GREY_LINE)

    page.draw_rect(fitz.Rect(MARGIN, 508, MARGIN + 120, 526), color=WHITE, fill=WHITE)
    _text(page, "CONFIDENTIAL", MARGIN + 8, 521, size=9, color=NAVY, bold=True)

    # Bottom white bar
    page.draw_rect(fitz.Rect(0, PAGE_H - 8, PAGE_W, PAGE_H), color=WHITE, fill=WHITE)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Table of Contents", "ProcureAI Discovery Report")
    y = _section_title(page, "Report Sections", y)

    sections = [
        ("1", "Discovery Strategy & Plan",      "Page 3"),
        ("2", "Ideal Customer Profile (ICP)",   "Page 4"),
        ("3", "Companies Found",                "Page 5"),
        ("4", "Company Validation & Scores",    "Page 6"),
        ("5", "Decision Makers",                "Page 7"),
        ("6", "Enriched Contacts",              "Page 7"),
        ("7", "Final Recommendations",          "Page 8"),
    ]

    y += 10
    for num, title, pg in sections:
        # Section row
        page.draw_rect(fitz.Rect(MARGIN, y - 2, PAGE_W - MARGIN, y + 20),
                       color=GREY_BG if int(num) % 2 == 0 else WHITE,
                       fill=GREY_BG if int(num) % 2 == 0 else WHITE)
        # Navy number badge
        page.draw_rect(fitz.Rect(MARGIN, y, MARGIN + 22, y + 18),
                       color=NAVY, fill=NAVY)
        _text(page, num,    MARGIN + 7,  y + 13, size=9,  color=WHITE, bold=True)
        _text(page, title,  MARGIN + 32, y + 13, size=10, color=DARK_TEXT)
        _text(page, pg,     PAGE_W - MARGIN - 55, y + 13, size=9, color=GREY_TEXT)
        # Dot leaders
        dots = "." * 55
        _text(page, dots,   MARGIN + 200, y + 13, size=9, color=GREY_LINE)
        y += 28

    # Summary stats row
    y += 20
    _thin_divider(page, y)
    y += 18
    _text(page, "DISCOVERY SUMMARY", MARGIN, y, size=10, color=NAVY, bold=True)
    y += 18

    companies_text = results.get("companies_found", "") or ""
    validated_text = results.get("validated_companies", "") or ""

    company_count = companies_text.count("COMPANY NAME")
    if not company_count:
        company_count = len(re.findall(r"COMPANY\s*\d+\s*:", validated_text))
    if not company_count:
        company_count = len(re.findall(r"COMPANY NAME\s*:", validated_text, re.I))

    shortlist_count = len(re.findall(r"Pursue Now|#1 Priority|#2 Priority|#3 Priority", validated_text, re.I))
    if not shortlist_count:
        shortlist_count = company_count

    _stat_card(page, "COMPANIES FOUND",     str(company_count or 0),   MARGIN,           y, accent=NAVY)
    _stat_card(page, "SHORTLISTED",         str(shortlist_count or 0), MARGIN + 125,     y, accent=GREEN)
    _stat_card(page, "TARGET INDUSTRY",     industry[:12],        MARGIN + 250,     y, accent=NAVY_LIGHT)
    _stat_card(page, "TARGET LOCATION",     location[:14],        MARGIN + 375,     y, accent=TEAL)

    _footer(page, 2, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — DISCOVERY STRATEGY & PLAN
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Discovery Strategy & Plan", "Section 1")
    y = _section_title(page, "AI-Generated Discovery Plan", y)

    y = _render_agent_output(page, results.get("plan", "N/A"), y, max_y=PAGE_H - 50)
    _footer(page, 3, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — IDEAL CUSTOMER PROFILE
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Ideal Customer Profile", "Section 2")

    # ICP hero banner
    page.draw_rect(fitz.Rect(MARGIN, y, PAGE_W - MARGIN, y + 48),
                   color=NAVY_LIGHT, fill=NAVY_LIGHT)
    _text(page, "ICP TARGET",  MARGIN + 14, y + 16, size=8,  color=GREY_LINE, bold=True)
    _text(page, f"{industry}  |  {location}  |  {size}",
          MARGIN + 14, y + 34, size=11, color=WHITE, bold=True)
    y += 62

    y = _section_title(page, "Ideal Customer Profile Definition", y)
    y = _render_agent_output(page, results.get("icp_profile", "N/A"), y, max_y=PAGE_H - 50)
    _footer(page, 4, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 — COMPANIES FOUND
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Companies Found", "Section 3")

    # Location badge
    page.draw_rect(fitz.Rect(MARGIN, y, MARGIN + 260, y + 28),
                   color=GREEN, fill=GREEN)
    _text(page, f"  Location Filter Applied: {location}",
          MARGIN + 8, y + 18, size=9, color=WHITE, bold=True)
    y += 40

    y = _section_title(page, f"Companies Identified in {location}", y)
    y = _render_agent_output(page, results.get("companies_found", "N/A"), y,
                             max_y=PAGE_H - 50)
    _footer(page, 5, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 6 — COMPANY VALIDATION & COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Company Validation & Scores", "Section 4")

    # Score legend
    legend_items = [
        ("80-100", "Strong Fit",    GREEN),
        ("60-79",  "Medium Fit",    AMBER),
        ("40-59",  "Weak Fit",      RED),
        ("< 40",   "No Fit",        GREY_TEXT),
        ("0",      "Disqualified",  (0.3, 0.3, 0.3)),
    ]
    lx = MARGIN
    for score_range, label, color in legend_items:
        page.draw_rect(fitz.Rect(lx, y, lx + 10, y + 10), color=color, fill=color)
        _text(page, f"{score_range}: {label}", lx + 14, y + 9, size=7.5, color=DARK_TEXT)
        lx += 92
    y += 22

    _thin_divider(page, y)
    y += 12

    y = _section_title(page, "Validation Results & Comparison", y)
    y = _render_agent_output(page, results.get("validated_companies", "N/A"), y,
                             max_y=PAGE_H - 50)
    _footer(page, 6, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 7 — DECISION MAKERS & ENRICHED CONTACTS
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Decision Makers & Contacts", "Sections 5 & 6")

    y = _section_title(page, "Decision Makers Identified", y)
    dm_text = results.get("decision_makers", "N/A")
    # Allow half the page for decision makers
    mid_y = y + (PAGE_H - y - 60) // 2
    y = _render_agent_output(page, dm_text, y, max_y=mid_y)

    _thin_divider(page, y + 6)
    y += 20

    y = _section_title(page, "Enriched Contact Intelligence", y, color=TEAL)
    y = _render_agent_output(page, results.get("enriched_contacts", "N/A"), y,
                             max_y=PAGE_H - 50)
    _footer(page, 7, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 8 — FINAL RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Final Recommendations", "Section 7")

    # Extract top prospect name for hero box
    rec_text   = _clean(results.get("recommendations", "N/A"))
    top_prospect = "See full analysis below"
    for line in rec_text.split("\n"):
        clean_line = line.strip()
        if any(kw in clean_line.lower() for kw in
               ["top prospect", "#1", "1st priority", "priority 1", "recommended vendor"]):
            parts = clean_line.split(":")
            if len(parts) > 1:
                top_prospect = parts[1].strip()[:55]
            break

    # Hero box — top prospect
    page.draw_rect(fitz.Rect(MARGIN, y, PAGE_W - MARGIN, y + 72),
                   color=NAVY, fill=NAVY)
    page.draw_rect(fitz.Rect(MARGIN, y, MARGIN + 6, y + 72), color=GREEN, fill=GREEN)
    _text(page, "TOP PROSPECT — CONTACT FIRST",
          MARGIN + 16, y + 20, size=8.5, color=GREY_LINE, bold=True)
    _text(page, top_prospect, MARGIN + 16, y + 48, size=17, color=WHITE, bold=True)
    y += 88

    y = _section_title(page, "Sales Playbook & Action Plan", y)
    y = _render_agent_output(page, results.get("recommendations", "N/A"), y,
                             max_y=PAGE_H - 120)

    # ── Approval Sign-off Box ─────────────────────────────────────────────────
    box_y = PAGE_H - 110
    page.draw_rect(fitz.Rect(MARGIN, box_y, PAGE_W - MARGIN, box_y + 62),
                   color=GREY_BG, fill=GREY_BG)
    page.draw_rect(fitz.Rect(MARGIN, box_y, PAGE_W - MARGIN, box_y + 62),
                   color=GREY_LINE, width=0.8)
    page.draw_rect(fitz.Rect(MARGIN, box_y, MARGIN + 4, box_y + 62),
                   color=NAVY, fill=NAVY)
    _text(page, "SALES MANAGER APPROVAL",
          MARGIN + 14, box_y + 18, size=9, color=NAVY, bold=True)
    _text(page, "Approved by: _______________________",
          MARGIN + 14, box_y + 36, size=9, color=DARK_TEXT)
    _text(page, "Date: ___________________",
          MARGIN + 260, box_y + 36, size=9, color=DARK_TEXT)
    _text(page, "Signature: _______________________",
          MARGIN + 14, box_y + 52, size=9, color=DARK_TEXT)

    _footer(page, 8, total_pages)

    return doc.tobytes()