import fitz
import re
from datetime import datetime

# ── Classic Corporate Color Palette ──────────────────────────────────────────
WHITE        = (1.0,  1.0,  1.0)
BLACK        = (0.1,  0.1,  0.1)
NAVY         = (0.10, 0.23, 0.42)   # #1a3a6b - headings
NAVY_LIGHT   = (0.18, 0.35, 0.58)   # slightly lighter navy for subheadings
GREY_BG      = (0.95, 0.96, 0.97)   # #f2f4f7 - alternating table rows
GREY_LINE    = (0.75, 0.78, 0.82)   # table borders
GREY_TEXT    = (0.35, 0.37, 0.40)   # secondary text
DARK_TEXT    = (0.10, 0.10, 0.10)   # body text
GREEN        = (0.07, 0.47, 0.24)   # #127a3d - positive
RED          = (0.70, 0.10, 0.10)   # risk red
YELLOW_BG    = (1.0,  0.97, 0.88)   # light amber for warnings
COVER_BG     = (0.10, 0.23, 0.42)   # navy cover background

PAGE_W = 595
PAGE_H = 842
MARGIN = 50
CONTENT_W = PAGE_W - MARGIN * 2


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _wrap_text(page, text, x, y, max_width, size=10, color=DARK_TEXT, line_height=15, max_y=800):
    """Word-wrap text. Returns final y."""
    words = str(text).split()
    line = ""
    cur_y = y
    for word in words:
        test = (line + " " + word).strip()
        if len(test) * size * 0.52 > max_width and line:
            if cur_y < max_y:
                try:
                    page.insert_text((x, cur_y), line, fontname="helv", fontsize=size, color=color)
                except Exception:
                    pass
            cur_y += line_height
            line = word
        else:
            line = test
    if line and cur_y < max_y:
        try:
            page.insert_text((x, cur_y), line, fontname="helv", fontsize=size, color=color)
        except Exception:
            pass
    return cur_y + line_height


def _divider(page, y, color=NAVY, width=1.0):
    page.draw_line((MARGIN, y), (PAGE_W - MARGIN, y), color=color, width=width)


def _thin_divider(page, y):
    page.draw_line((MARGIN, y), (PAGE_W - MARGIN, y), color=GREY_LINE, width=0.5)


def _section_title(page, title, y):
    """Draw a navy section title with underline."""
    _text(page, title.upper(), MARGIN, y, size=13, color=NAVY, bold=True)
    y += 6
    _divider(page, y, color=NAVY, width=1.5)
    return y + 14


def _footer(page, page_num, total):
    _thin_divider(page, PAGE_H - 35)
    _text(page, "ProcureAI - Confidential Procurement Report", MARGIN, PAGE_H - 20, size=8, color=GREY_TEXT)
    _text(page, f"Page {page_num} of {total}", PAGE_W - MARGIN - 55, PAGE_H - 20, size=8, color=GREY_TEXT)
    _text(page, datetime.now().strftime("%B %d, %Y"), PAGE_W // 2 - 35, PAGE_H - 20, size=8, color=GREY_TEXT)


def _header_bar(page, title, subtitle=""):
    """Top navy bar for inner pages."""
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, 58), color=NAVY, fill=NAVY)
    _text(page, "ProcureAI", MARGIN, 22, size=10, color=WHITE, bold=True)
    _text(page, title, MARGIN, 42, size=16, color=WHITE, bold=True)
    if subtitle:
        _text(page, subtitle, PAGE_W - MARGIN - len(subtitle) * 5.5, 42, size=9, color=GREY_LINE)
    return 78


def _clean(text):
    if not text:
        return "N/A"
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s?', '', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    # remove non-latin characters that PyMuPDF helv can't render
    text = text.encode('latin-1', errors='replace').decode('latin-1')
    return text.strip()


# ── Table Parser ──────────────────────────────────────────────────────────────

def _parse_markdown_table(text):
    """
    Extracts a markdown table from text.
    Returns (headers, rows) or (None, None) if no table found.
    """
    lines = text.split('\n')
    table_lines = []
    in_table = False

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
        parts = [c.strip() for c in line.strip('|').split('|')]
        return parts

    headers = parse_row(table_lines[0])
    rows = []
    for line in table_lines[2:]:  # skip separator line
        if line.startswith('|'):
            rows.append(parse_row(line))

    return headers, rows


def _draw_table(page, headers, rows, x, y, max_y=800):
    """Draw a proper bordered table. Returns final y."""
    if not headers:
        return y

    n_cols = len(headers)
    col_w = CONTENT_W / n_cols
    row_h = 18
    header_h = 22

    # Header row background
    page.draw_rect(
        fitz.Rect(x, y, x + CONTENT_W, y + header_h),
        color=NAVY, fill=NAVY
    )
    for i, h in enumerate(headers):
        _text(page, str(h)[:22], x + i * col_w + 4, y + 14, size=8, color=WHITE, bold=True)

    y += header_h

    # Data rows
    for r_idx, row in enumerate(rows):
        if y + row_h > max_y:
            break
        bg = GREY_BG if r_idx % 2 == 0 else WHITE
        page.draw_rect(fitz.Rect(x, y, x + CONTENT_W, y + row_h), color=bg, fill=bg)
        for i, cell in enumerate(row[:n_cols]):
            cell_text = str(cell)[:28]
            _text(page, cell_text, x + i * col_w + 4, y + 12, size=8, color=DARK_TEXT)
        # row bottom border
        page.draw_line((x, y + row_h), (x + CONTENT_W, y + row_h), color=GREY_LINE, width=0.3)
        y += row_h

    # Outer border
    page.draw_rect(
        fitz.Rect(x, y - row_h * len(rows[:20]) - header_h,
                  x + CONTENT_W, y),
        color=GREY_LINE, width=0.8
    )
    # Column dividers
    start_y = y - row_h * len(rows[:20]) - header_h
    for i in range(1, n_cols):
        cx = x + i * col_w
        page.draw_line((cx, start_y), (cx, y), color=GREY_LINE, width=0.3)

    return y + 10


def _render_agent_output(page, text, y, max_y=790):
    """
    Render agent text output:
    - If it contains a markdown table, draw it as a proper table
    - Then render remaining text as structured paragraphs
    """
    text = _clean(text)
    lines = text.split('\n')

    # Check for table
    headers, rows = _parse_markdown_table(text)
    if headers and rows:
        y = _draw_table(page, headers, rows, MARGIN, y, max_y=max_y)
        y += 8

    # Render non-table lines
    for line in lines:
        line = line.strip()
        if not line:
            y += 4
            continue
        if line.startswith('|'):
            continue  # skip table lines already rendered

        # Numbered heading like "1. Title" or "**Title**"
        if re.match(r'^[1-9]\.\s', line) or re.match(r'^\*\*.*\*\*$', line):
            heading = re.sub(r'^\d+\.\s*', '', line)
            heading = re.sub(r'\*\*(.*?)\*\*', r'\1', heading)
            y += 6
            if y > max_y:
                break
            _text(page, heading, MARGIN, y, size=10, color=NAVY, bold=True)
            y += 14
        elif line.startswith('-') or line.startswith('*'):
            bullet = line.lstrip('-* ').strip()
            if y > max_y:
                break
            _text(page, '•', MARGIN, y, size=10, color=NAVY, bold=True)
            y = _wrap_text(page, bullet, MARGIN + 14, y, CONTENT_W - 14,
                           size=9.5, color=DARK_TEXT, line_height=14, max_y=max_y)
        else:
            if y > max_y:
                break
            y = _wrap_text(page, line, MARGIN, y, CONTENT_W,
                           size=9.5, color=DARK_TEXT, line_height=14, max_y=max_y)
        y += 2

    return y


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
    doc = fitz.open()
    total_pages = 5

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — COVER (Navy Background)
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=False)

    # Top white accent bar
    page.draw_rect(fitz.Rect(0, 0, PAGE_W, 8), color=WHITE, fill=WHITE)

    # Logo area
    page.draw_rect(fitz.Rect(MARGIN, 120, MARGIN + 80, 180), color=WHITE, fill=WHITE)
    _text(page, "AI", MARGIN + 18, 162, size=30, color=NAVY, bold=True)

    # Title
    _text(page, "ProcureAI", MARGIN, 220, size=36, color=WHITE, bold=True)
    _text(page, "Procurement Intelligence Report", MARGIN, 255, size=16, color=GREY_LINE)

    # Thin white line
    page.draw_line((MARGIN, 275), (PAGE_W - MARGIN, 275), color=WHITE, width=0.8)

    # Meta info box
    page.draw_rect(fitz.Rect(MARGIN, 295, PAGE_W - MARGIN, 430), color=NAVY_LIGHT, fill=NAVY_LIGHT)

    _text(page, "VENDORS ANALYZED", MARGIN + 20, 320, size=9, color=GREY_LINE, bold=True)
    vendor_str = ", ".join(vendor_names)
    if len(vendor_str) > 65:
        vendor_str = vendor_str[:62] + "..."
    _text(page, vendor_str, MARGIN + 20, 340, size=10, color=WHITE)

    _text(page, "TOTAL VENDORS", MARGIN + 20, 370, size=9, color=GREY_LINE, bold=True)
    _text(page, str(len(vendor_names)), MARGIN + 20, 392, size=24, color=WHITE, bold=True)

    _text(page, "DATE GENERATED", PAGE_W // 2, 370, size=9, color=GREY_LINE, bold=True)
    _text(page, datetime.now().strftime("%B %d, %Y"), PAGE_W // 2, 392, size=11, color=WHITE)

    # Powered by
    _text(page, "Powered by LangGraph  |  LLaMA 3.3 70B  |  FastAPI  |  Groq",
          MARGIN, 480, size=9, color=GREY_LINE)

    # Confidential label
    page.draw_rect(fitz.Rect(MARGIN, 520, MARGIN + 120, 538), color=WHITE, fill=WHITE)
    _text(page, "CONFIDENTIAL", MARGIN + 8, 533, size=9, color=NAVY, bold=True)

    # Bottom white bar
    page.draw_rect(fitz.Rect(0, PAGE_H - 8, PAGE_W, PAGE_H), color=WHITE, fill=WHITE)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — VENDOR COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Vendor Comparison", "Section 1")
    y = _section_title(page, "Side-by-Side Vendor Analysis", y)

    comparison_text = results.get("comparison", "N/A")
    y = _render_agent_output(page, comparison_text, y, max_y=PAGE_H - 50)

    _footer(page, 2, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — RISK ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Risk Analysis", "Section 2")
    y = _section_title(page, "Vendor Risk Assessment", y)

    # Risk summary cards for each vendor
    risk_text = _clean(results.get("risks", "N/A"))
    card_w = (CONTENT_W - 20) // 3
    card_h = 55
    card_y = y

    for i, vendor in enumerate(vendor_names[:6]):
        col = i % 3
        row = i // 3
        cx = MARGIN + col * (card_w + 10)
        cy = card_y + row * (card_h + 8)

        vendor_lower = vendor.lower()
        risk_color = GREEN
        risk_label = "Low Risk"
        idx = risk_text.lower().find(vendor_lower)
        if idx >= 0:
            snippet = risk_text[idx:idx+300].lower()
            if "high" in snippet:
                risk_color = RED
                risk_label = "High Risk"
            elif "medium" in snippet or "moderate" in snippet:
                risk_color = (0.75, 0.45, 0.0)
                risk_label = "Medium Risk"

        # Card border
        page.draw_rect(fitz.Rect(cx, cy, cx + card_w, cy + card_h), color=GREY_LINE, width=1.0)
        # Left color bar
        page.draw_rect(fitz.Rect(cx, cy, cx + 4, cy + card_h), color=risk_color, fill=risk_color)
        _text(page, vendor[:18], cx + 10, cy + 16, size=9, color=DARK_TEXT, bold=True)
        _text(page, risk_label, cx + 10, cy + 30, size=8, color=risk_color, bold=True)

    rows_used = (min(len(vendor_names), 6) + 2) // 3
    y = card_y + rows_used * (card_h + 8) + 18

    _thin_divider(page, y)
    y += 14

    y = _section_title(page, "Detailed Risk Findings", y)
    y = _render_agent_output(page, results.get("risks", "N/A"), y, max_y=PAGE_H - 50)

    _footer(page, 3, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — NEGOTIATION STRATEGIES
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Negotiation Strategies", "Section 3")
    y = _section_title(page, "Vendor Negotiation Playbook", y)

    y = _render_agent_output(page, results.get("negotiation", "N/A"), y, max_y=PAGE_H - 50)

    _footer(page, 4, total_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 — FINAL RECOMMENDATION
    # ══════════════════════════════════════════════════════════════════════════
    page = _new_page(doc, white=True)
    y = _header_bar(page, "Final Recommendation", "Section 4")
    y = _section_title(page, "AI Procurement Decision", y)

    rec_text = _clean(results.get("recommendation", "N/A"))

    # Extract recommended vendor
    rec_vendor = "See full analysis below"
    for line in rec_text.split("\n"):
        if "recommended vendor" in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                rec_vendor = parts[1].strip()[:50]
            break

    # Hero recommendation box
    page.draw_rect(fitz.Rect(MARGIN, y, PAGE_W - MARGIN, y + 70), color=NAVY, fill=NAVY)
    page.draw_rect(fitz.Rect(MARGIN, y, MARGIN + 5, y + 70), color=GREEN, fill=GREEN)
    _text(page, "RECOMMENDED VENDOR", MARGIN + 14, y + 20, size=9, color=GREY_LINE, bold=True)
    _text(page, rec_vendor, MARGIN + 14, y + 46, size=18, color=WHITE, bold=True)

    y += 86

    # Render full recommendation text
    y = _render_agent_output(page, results.get("recommendation", "N/A"), y, max_y=PAGE_H - 70)

    # Approval box at the bottom
    box_y = PAGE_H - 110
    page.draw_rect(fitz.Rect(MARGIN, box_y, PAGE_W - MARGIN, box_y + 60), color=GREY_BG, fill=GREY_BG)
    page.draw_rect(fitz.Rect(MARGIN, box_y, PAGE_W - MARGIN, box_y + 60), color=GREY_LINE, width=0.8)
    _text(page, "PROCUREMENT MANAGER APPROVAL", MARGIN + 14, box_y + 18, size=9, color=NAVY, bold=True)
    _text(page, "Approved by: _______________________", MARGIN + 14, box_y + 36, size=9, color=DARK_TEXT)
    _text(page, "Date: _______________________", MARGIN + 250, box_y + 36, size=9, color=DARK_TEXT)
    _text(page, "Signature: _______________________", MARGIN + 14, box_y + 52, size=9, color=DARK_TEXT)

    _footer(page, 5, total_pages)

    return doc.tobytes()