from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

INK = "#10233F"
TEAL = "#16A6A1"
BLUE = "#4E79A7"
GOLD = "#F4B942"
RED = "#C63D4F"
PAPER = "#F5F7FB"
MUTED = "#60758F"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def center_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    title_color: str = INK,
    title_size: int = 33,
    subtitle_size: int = 23,
) -> None:
    x1, y1, x2, y2 = box
    title_font = font(title_size, bold=True)
    subtitle_font = font(subtitle_size)
    title_box = draw.textbbox((0, 0), title, font=title_font)
    subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    title_width = title_box[2] - title_box[0]
    subtitle_width = subtitle_box[2] - subtitle_box[0]
    center_y = (y1 + y2) // 2
    draw.text(
        ((x1 + x2 - title_width) // 2, center_y - 38), title, fill=title_color, font=title_font
    )
    draw.text(
        ((x1 + x2 - subtitle_width) // 2, center_y + 10),
        subtitle,
        fill=MUTED,
        font=subtitle_font,
    )


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int]) -> None:
    draw.line([start, end], fill=TEAL, width=8)
    x, y = end
    draw.polygon([(x, y), (x - 22, y - 14), (x - 22, y + 14)], fill=TEAL)


def architecture() -> None:
    image = Image.new("RGB", (2400, 1350), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((70, 60, 2330, 240), radius=34, fill=INK)
    draw.text((125, 105), "RISK PULSE", font=font(30, bold=True), fill=GOLD)
    draw.text(
        (125, 150),
        "Auditable financial risk intelligence - source to portfolio impact",
        font=font(45, bold=True),
        fill=WHITE,
    )

    boxes = {
        "gdelt": (90, 345, 420, 515),
        "bluesky": (90, 550, 420, 720),
        "replay": (90, 755, 420, 925),
        "ingest": (555, 430, 895, 625),
        "entity": (555, 675, 895, 870),
        "nlp": (1035, 470, 1435, 820),
        "signals": (1575, 345, 1945, 540),
        "api": (1575, 630, 1945, 825),
        "stress": (2010, 430, 2310, 650),
        "dashboard": (2010, 725, 2310, 945),
    }
    for key in ("gdelt", "bluesky", "replay"):
        draw.rounded_rectangle(boxes[key], radius=28, fill=WHITE, outline="#D8E1EC", width=3)
    center_text(draw, boxes["gdelt"], "GDELT", "news metadata")
    center_text(draw, boxes["bluesky"], "BLUESKY", "public social posts")
    center_text(draw, boxes["replay"], "REPLAY", "offline evidence")

    draw.rounded_rectangle(boxes["ingest"], radius=28, fill="#EAF8F7", outline=TEAL, width=4)
    draw.rounded_rectangle(boxes["entity"], radius=28, fill=WHITE, outline="#D8E1EC", width=3)
    center_text(draw, boxes["ingest"], "INGEST + NORMALIZE", "validate / deduplicate")
    center_text(draw, boxes["entity"], "ENTITY LINKING", "issuer / ticker / market")

    draw.rounded_rectangle(boxes["nlp"], radius=34, fill=INK)
    draw.text((1090, 515), "AI / NLP RISK ENGINE", font=font(35, bold=True), fill=WHITE)
    for index, (label, color) in enumerate(
        (
            ("Financial sentiment", TEAL),
            ("Event classification", BLUE),
            ("Impact severity 1-10", GOLD),
        )
    ):
        y = 595 + index * 72
        draw.ellipse((1095, y, 1121, y + 26), fill=color)
        draw.text((1145, y - 3), label, font=font(24), fill=WHITE)
    draw.text((1092, 775), "confidence + evidence + version", font=font(21), fill="#A9BED3")

    for key in ("signals", "api"):
        draw.rounded_rectangle(boxes[key], radius=28, fill=WHITE, outline="#D8E1EC", width=3)
    center_text(draw, boxes["signals"], "SIGNAL STORE", "SQLite / JSONL")
    center_text(draw, boxes["api"], "FASTAPI", "OpenAPI / filters")

    draw.rounded_rectangle(boxes["stress"], radius=28, fill="#FFF5DC", outline=GOLD, width=4)
    draw.rounded_rectangle(boxes["dashboard"], radius=28, fill="#EAF8F7", outline=TEAL, width=4)
    center_text(
        draw,
        boxes["stress"],
        "STRESS ENGINE",
        "loans / bonds / derivatives",
        title_size=27,
        subtitle_size=18,
    )
    center_text(
        draw,
        boxes["dashboard"],
        "ANALYST UI",
        "signals / drivers / quality",
        title_size=28,
        subtitle_size=18,
    )

    for key, target_y in (("gdelt", 495), ("bluesky", 525), ("replay", 555)):
        source = boxes[key]
        arrow(
            draw,
            (source[2] + 10, (source[1] + source[3]) // 2),
            (boxes["ingest"][0] - 20, target_y),
        )
    arrow(draw, (725, 635), (725, 665))
    arrow(draw, (905, 772), (1025, 650))
    arrow(draw, (1445, 580), (1565, 445))
    arrow(draw, (1760, 550), (1760, 620))
    arrow(draw, (1955, 445), (2000, 530))
    arrow(draw, (1955, 730), (2000, 825))
    arrow(draw, (2180, 660), (2180, 715))

    draw.rounded_rectangle(
        (90, 1060, 2310, 1240), radius=30, fill=WHITE, outline="#D8E1EC", width=3
    )
    draw.text((145, 1097), "CONTROL PLANE", font=font(28, bold=True), fill=INK)
    controls = [
        "data lineage + hashes",
        "model/config versions",
        "confidence gates",
        "structured logs + health",
        "tests + CI + Docker",
    ]
    x = 145
    for item in controls:
        width = draw.textbbox((0, 0), item, font=font(23))[2] + 55
        draw.rounded_rectangle((x, 1150, x + width, 1202), radius=20, fill="#EDF2F7")
        draw.text((x + 25, 1163), item, font=font(23), fill=MUTED)
        x += width + 28

    image.save(DOCS / "architecture.png", quality=95)


def dashboard_preview() -> None:
    image = Image.new("RGB", (2400, 1350), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 400, 1350), fill=INK)
    draw.text((65, 70), "RISK PULSE", font=font(38, bold=True), fill=GOLD)
    draw.text((65, 120), "Financial risk intelligence", font=font(23), fill="#B9C9D8")
    draw.rounded_rectangle((55, 215, 345, 285), radius=20, fill=TEAL)
    draw.text((90, 235), "RUN DEMO REPLAY", font=font(24, bold=True), fill=WHITE)
    for index, item in enumerate(
        ("Overview", "Signal explorer", "Stress lab", "Portfolio", "Model quality")
    ):
        y = 380 + index * 88
        fill = WHITE if index == 0 else "#A9BED3"
        draw.text((75, y), item, font=font(27, bold=index == 0), fill=fill)

    draw.rounded_rectangle((455, 55, 2330, 260), radius=34, fill=INK)
    draw.text((520, 95), "FROM NARRATIVE NOISE", font=font(25, bold=True), fill=GOLD)
    draw.text((520, 140), "TO PORTFOLIO IMPACT.", font=font(54, bold=True), fill=WHITE)
    draw.text(
        (520, 205),
        "entity-aware signals  |  auditable AI  |  transparent scenarios",
        font=font(25),
        fill="#B9C9D8",
    )

    kpis = [
        ("DOCUMENTS", "8", TEAL),
        ("SIGNALS", "9", BLUE),
        ("ACTIONABLE", "8", GOLD),
        ("STRESS RUNS", "4", RED),
    ]
    for index, (label, value, color) in enumerate(kpis):
        x = 455 + index * 470
        draw.rounded_rectangle(
            (x, 310, x + 420, 500), radius=28, fill=WHITE, outline="#D8E1EC", width=3
        )
        draw.rectangle((x, 310, x + 12, 500), fill=color)
        draw.text((x + 45, 345), label, font=font(22, bold=True), fill=MUTED)
        draw.text((x + 45, 395), value, font=font(62, bold=True), fill=INK)

    draw.rounded_rectangle(
        (455, 555, 1390, 1260), radius=30, fill=WHITE, outline="#D8E1EC", width=3
    )
    draw.text((510, 605), "LATEST RISK SIGNALS", font=font(27, bold=True), fill=INK)
    rows = [
        ("Nova Bank", "CREDIT EVENT", "8.9", RED),
        ("Market-wide", "MACROECONOMIC", "8.1", GOLD),
        ("Helios Energy", "OPERATIONAL / CYBER", "8.6", RED),
        ("Vertex Telecom", "REGULATORY / LEGAL", "7.8", GOLD),
    ]
    for index, (entity, event, impact, color) in enumerate(rows):
        y = 680 + index * 130
        draw.rounded_rectangle((505, y, 1340, y + 98), radius=20, fill="#F8FAFC")
        draw.ellipse((535, y + 32, 565, y + 62), fill=color)
        draw.text((590, y + 18), entity, font=font(28, bold=True), fill=INK)
        draw.text((590, y + 56), event, font=font(20), fill=MUTED)
        draw.text((1220, y + 28), impact, font=font(32, bold=True), fill=color)

    draw.rounded_rectangle(
        (1440, 555, 2330, 1260), radius=30, fill=WHITE, outline="#D8E1EC", width=3
    )
    draw.text((1495, 605), "PORTFOLIO STRESS", font=font(27, bold=True), fill=INK)
    draw.text((1495, 665), "Credit deterioration", font=font(34, bold=True), fill=INK)
    draw.text((1495, 715), "impact trigger 8.9 / 10", font=font(23), fill=MUTED)
    draw.text((1495, 800), "PRE-STRESS", font=font(20, bold=True), fill=MUTED)
    draw.text((1495, 840), "$411.8M", font=font(48, bold=True), fill=INK)
    draw.text((1900, 800), "SCENARIO P&L", font=font(20, bold=True), fill=MUTED)
    draw.text((1900, 840), "-$7.4M", font=font(48, bold=True), fill=RED)
    bars = [("Loans", 0.38), ("Bonds", 0.92), ("Derivatives", 0.55)]
    for index, (label, portion) in enumerate(bars):
        y = 980 + index * 76
        draw.text((1495, y), label, font=font(22), fill=MUTED)
        draw.rounded_rectangle((1690, y + 2, 2220, y + 32), radius=15, fill="#E4EAF1")
        draw.rounded_rectangle(
            (1690, y + 2, 1690 + int(530 * portion), y + 32), radius=15, fill=RED
        )
    draw.text(
        (1495, 1200), "Illustrative - not regulatory stress testing", font=font(20), fill=MUTED
    )

    image.save(DOCS / "dashboard_preview.png", quality=95)


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    architecture()
    dashboard_preview()
    print("Exported docs/architecture.png and docs/dashboard_preview.png")


if __name__ == "__main__":
    main()
