from pathlib import Path
import re
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image as PdfImage,
    PageTemplate,
    Paragraph,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"
IMAGES.mkdir(parents=True, exist_ok=True)

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#2367A8")
TEAL = colors.HexColor("#147D78")
PALE = colors.HexColor("#EAF2F8")
INK = colors.HexColor("#202A33")
MUTED = colors.HexColor("#5D6B78")


def font(size, bold=False, mono=False):
    candidates = []
    if mono:
        candidates = [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
        ]
    elif bold:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


def draw_console_demo(path):
    width, height = 1500, 860
    image = Image.new("RGB", (width, height), "#101418")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, width - 24, height - 24), radius=22, fill="#171D22", outline="#33414D", width=3)
    draw.rectangle((24, 24, width - 24, 88), fill="#222B32")
    for x, color in [(58, "#FF5F57"), (94, "#FEBC2E"), (130, "#28C840")]:
        draw.ellipse((x - 12, 44, x + 12, 68), fill=color)
    draw.text((180, 43), "ContrastCheck - Version 1 demonstration", font=font(27, bold=True), fill="#E7EDF2")

    lines = [
        ("$ FIGMA_TOKEN=******** python3 main.py", "#A8D7FF"),
        ("============================================================", "#7E8B95"),
        ("  CONTRASTCHECK - Figma Accessibility Checker", "#FFFFFF"),
        ("============================================================", "#7E8B95"),
        ("Connecting to Figma API...", "#E7EDF2"),
        ("Connected successfully!", "#6EE7A0"),
        ("Scanning page: Interview Protocol", "#E7EDF2"),
        ("Scanning page: Hi-Fi Design", "#E7EDF2"),
        ("Found text nodes across all pages.", "#E7EDF2"),
        ("PASS | ratio 21.00 | Primary heading | FG (0, 0, 0)", "#6EE7A0"),
        ("FAIL | ratio 2.85 | Secondary label | FG (160, 160, 160)", "#FF8585"),
        ("PASS | ratio 7.46 | Button label | FG (70, 70, 70)", "#6EE7A0"),
        ("SUMMARY: 2 passed, 1 failed", "#FFD166"),
        ("Report saved to report.txt", "#A8D7FF"),
    ]
    y = 125
    mono = font(26, mono=True)
    for text, color in lines:
        draw.text((70, y), text, font=mono, fill=color)
        y += 47
    image.save(path)


def draw_flow(path):
    width, height = 1500, 520
    image = Image.new("RGB", (width, height), "#F4F8FB")
    draw = ImageDraw.Draw(image)
    title = font(34, bold=True)
    label = font(24, bold=True)
    small = font(20)
    draw.text((55, 35), "ContrastCheck Version 1 processing flow", font=title, fill="#17324D")
    boxes = [
        (50, 150, 285, 330, "Figma API", "Retrieve file JSON", "#DDEEFF"),
        (350, 150, 585, 330, "Recursive scan", "Find text + fills", "#DDF3EE"),
        (650, 150, 885, 330, "WCAG math", "Luminance + ratio", "#FFF0D8"),
        (950, 150, 1185, 330, "Report", "Pass, fail, totals", "#EAE2F8"),
        (1250, 150, 1450, 330, "Version 2", "Real backgrounds", "#F9DFE4"),
    ]
    for index, (x1, y1, x2, y2, heading, detail, fill) in enumerate(boxes):
        draw.rounded_rectangle((x1, y1, x2, y2), radius=20, fill=fill, outline="#6B7C8A", width=3)
        draw.text((x1 + 22, y1 + 42), heading, font=label, fill="#17324D")
        draw.text((x1 + 22, y1 + 98), detail, font=small, fill="#34495A")
        if index < len(boxes) - 1:
            start = (x2 + 12, (y1 + y2) // 2)
            end = (boxes[index + 1][0] - 14, (y1 + y2) // 2)
            draw.line((start, end), fill="#2367A8", width=6)
            draw.polygon([(end[0], end[1]), (end[0] - 16, end[1] - 10), (end[0] - 16, end[1] + 10)], fill="#2367A8")
    draw.rounded_rectangle((1030, 380, 1450, 468), radius=18, fill="#FFFFFF", outline="#C05A6E", width=3)
    draw.text((1050, 398), "Current limitation: white default background", font=small, fill="#8F3046")
    image.save(path)


def inline_markup(text):
    value = escape(text)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', value)
    return value


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=NAVY, alignment=TA_LEFT, spaceAfter=16),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=BLUE, spaceBefore=12, spaceAfter=7),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=9, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.4, textColor=INK, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName="Helvetica", fontSize=9.3, leading=13, leftIndent=17, firstLineIndent=-9, bulletIndent=7, textColor=INK, spaceAfter=3),
        "caption": ParagraphStyle("Caption", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8.3, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceAfter=8),
        "meta": ParagraphStyle("Meta", parent=base["BodyText"], fontName="Helvetica", fontSize=9, leading=13, textColor=MUTED, spaceAfter=3),
    }


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, letter[1] - 0.32 * inch, letter[0], 0.32 * inch, fill=True, stroke=False)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.7 * inch, 0.38 * inch, "ContrastCheck - HCI 584 - Heeral Chumber")
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


def markdown_to_story(markdown_path, styles):
    story = []
    for raw in markdown_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 3))
        elif line.startswith("# "):
            story.append(Paragraph(inline_markup(line[2:]), styles["title"]))
            story.append(Spacer(1, 3))
        elif line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), styles["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), styles["h3"]))
        elif line.startswith("- "):
            story.append(Paragraph(inline_markup(line[2:]), styles["bullet"], bulletText="-"))
        elif line.startswith("!["):
            match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            if match:
                image_path = markdown_path.parent / match.group(2)
                pdf_image = PdfImage(str(image_path))
                max_width = 6.95 * inch
                max_height = 3.7 * inch
                scale = min(max_width / pdf_image.imageWidth, max_height / pdf_image.imageHeight)
                pdf_image.drawWidth = pdf_image.imageWidth * scale
                pdf_image.drawHeight = pdf_image.imageHeight * scale
                pdf_image.hAlign = "CENTER"
                story.append(Spacer(1, 4))
                story.append(pdf_image)
                story.append(Spacer(1, 4))
        elif line.startswith("**Student:") or line.startswith("**Course:") or line.startswith("**Project:") or line.startswith("**Revision purpose:"):
            story.append(Paragraph(inline_markup(line.replace("  ", "")), styles["meta"]))
        elif line.startswith("**Figure"):
            story.append(Paragraph(inline_markup(line), styles["caption"]))
        else:
            story.append(Paragraph(inline_markup(line), styles["body"]))
    return story


def build_pdf(markdown_name, pdf_name):
    styles = build_styles()
    output = DOCS / pdf_name
    doc = BaseDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title=pdf_name.replace("-", " ").replace(".pdf", "").title(),
        author="Heeral Chumber",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=header_footer))
    doc.build(markdown_to_story(DOCS / markdown_name, styles))
    return output


if __name__ == "__main__":
    draw_console_demo(IMAGES / "version1-console-demo.png")
    draw_flow(IMAGES / "version1-flow.png")
    outputs = [
        build_pdf("version1-review.md", "version1-review.pdf"),
        build_pdf("revised-project-spec.md", "revised-project-spec.pdf"),
    ]
    for output in outputs:
        print(output)
