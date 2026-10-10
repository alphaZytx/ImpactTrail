from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from impacttrail.config import Settings
from impacttrail.ingestion.replay import ReplayAdapter
from impacttrail.nlp.sentiment import LexiconSentimentAnalyzer
from impacttrail.services.pipeline import RiskPipeline
from impacttrail.storage.repositories import Repository

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUTPUT = ROOT / "output/pdf"
CANONICAL = OUTPUT / "ImpactTrail_Presentation.pdf"
REPO_COPY = DOCS / "presentation.pdf"

PAGE_SIZE = landscape((540, 960))
WIDTH, HEIGHT = PAGE_SIZE

INK = HexColor("#10233F")
TEAL = HexColor("#16A6A1")
BLUE = HexColor("#4E79A7")
GOLD = HexColor("#F4B942")
RED = HexColor("#C63D4F")
PAPER = HexColor("#F5F7FB")
MUTED = HexColor("#60758F")
WHITE = HexColor("#FFFFFF")
LINE = HexColor("#D8E1EC")


def set_fill(pdf: canvas.Canvas, color: Any) -> None:
    pdf.setFillColor(color)


def wrapped_lines(text: str, face: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if stringWidth(candidate, face, size) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    size: float = 18,
    leading: float | None = None,
    color: Any = INK,
    face: str = "Helvetica",
) -> float:
    leading = leading or size * 1.32
    pdf.setFont(face, size)
    set_fill(pdf, color)
    for line in wrapped_lines(text, face, size, width):
        pdf.drawString(x, y, line)
        y -= leading
    return y


def draw_bullets(
    pdf: canvas.Canvas, items: list[str], x: float, y: float, width: float, size: float = 17
) -> float:
    for item in items:
        set_fill(pdf, TEAL)
        pdf.circle(x + 5, y + 5, 4, stroke=0, fill=1)
        y = draw_wrapped(pdf, item, x + 20, y, width - 20, size=size, color=INK)
        y -= 13
    return y


def title(pdf: canvas.Canvas, eyebrow: str, heading: str, subtitle: str | None = None) -> None:
    pdf.setFont("Helvetica-Bold", 14)
    set_fill(pdf, TEAL)
    pdf.drawString(48, HEIGHT - 47, eyebrow.upper())
    pdf.setFont("Helvetica-Bold", 30)
    set_fill(pdf, INK)
    pdf.drawString(48, HEIGHT - 87, heading)
    if subtitle:
        draw_wrapped(pdf, subtitle, 48, HEIGHT - 112, WIDTH - 96, size=13, color=MUTED)


def footer(pdf: canvas.Canvas, slide: int, dark: bool = False) -> None:
    color = HexColor("#A9BED3") if dark else MUTED
    pdf.setFont("Helvetica", 9)
    set_fill(pdf, color)
    pdf.drawString(48, 24, "ImpactTrail | Educational prototype - not investment advice")
    pdf.drawRightString(WIDTH - 48, 24, f"{slide} / 7")


def rounded_card(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: Any = WHITE,
    stroke: Any = LINE,
) -> None:
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(1)
    pdf.roundRect(x, y, width, height, 14, stroke=1, fill=1)


def metric_card(
    pdf: canvas.Canvas, x: float, y: float, width: float, label: str, value: str, color: Any
) -> None:
    rounded_card(pdf, x, y, width, 88)
    pdf.setFillColor(color)
    pdf.roundRect(x, y, 7, 88, 4, stroke=0, fill=1)
    pdf.setFont("Helvetica-Bold", 10)
    set_fill(pdf, MUTED)
    pdf.drawString(x + 18, y + 60, label.upper())
    pdf.setFont("Helvetica-Bold", 28)
    set_fill(pdf, INK)
    pdf.drawString(x + 18, y + 22, value)


def load_results() -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Build deck evidence from an isolated deterministic replay, never mutable demo state."""
    with tempfile.TemporaryDirectory(prefix="impacttrail-deck-") as directory:
        settings = Settings(
            env="test",
            database_url=f"sqlite:///{Path(directory) / 'presentation.db'}",
            model_backend="lexicon",
        )
        repository = Repository(settings.database_url)
        pipeline = RiskPipeline(settings, repository, LexiconSentimentAnalyzer())
        fixture = settings.project_root / "data/demo/mixed_source_events.jsonl"
        summary = asyncio.run(pipeline.process_adapter(ReplayAdapter(fixture)))
        metrics = {**repository.metrics(), "replay_summary": summary.as_dict()}
        credit_signal = next(
            (
                signal
                for signal in repository.list_signals(limit=100)[0]
                if signal.event.label.value == "credit_event"
            ),
            None,
        )
        stress = repository.get_stress_run_for_signal(credit_signal) if credit_signal else None
        return metrics, stress.model_dump(mode="json") if stress else None


def load_evaluation() -> dict[str, Any]:
    metrics_path = DOCS / "results/model_metrics.json"
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def slide_1(pdf: canvas.Canvas, metrics: dict[str, Any]) -> None:
    pdf.setFillColor(INK)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    pdf.setFillColor(TEAL)
    pdf.circle(770, 410, 150, stroke=0, fill=1)
    pdf.setFillColor(BLUE)
    pdf.circle(875, 125, 80, stroke=0, fill=1)
    pdf.setFillColor(GOLD)
    pdf.circle(860, 475, 18, stroke=0, fill=1)
    pdf.setFont("Helvetica-Bold", 17)
    set_fill(pdf, GOLD)
    pdf.drawString(62, 465, "S&P GLOBAL & CRISIL CAMPUS HACKATHON 2026")
    pdf.setFont("Helvetica-Bold", 53)
    set_fill(pdf, WHITE)
    pdf.drawString(62, 365, "IMPACTTRAIL")
    pdf.setFont("Helvetica-Bold", 29)
    pdf.drawString(62, 318, "From narrative noise to portfolio impact")
    draw_wrapped(
        pdf,
        "Auditable financial risk signals from news and social text, connected directly to "
        "transparent wholesale-portfolio stress testing.",
        62,
        268,
        650,
        size=18,
        leading=25,
        color=HexColor("#C8D6E5"),
    )
    candidate = os.getenv("IMPACTTRAIL_CANDIDATE_NAME", "Alok Chandra")
    college = os.getenv("IMPACTTRAIL_COLLEGE", "College name to be added before submission")
    pdf.setFont("Helvetica-Bold", 13)
    set_fill(pdf, WHITE)
    pdf.drawString(62, 163, candidate)
    pdf.setFont("Helvetica", 12)
    set_fill(pdf, HexColor("#A9BED3"))
    pdf.drawString(62, 143, college)
    badges = [
        f"{metrics.get('documents', 0)} unique documents",
        f"{metrics.get('signals', 0)} risk signals",
        f"{metrics.get('stress_runs', 0)} stress runs",
    ]
    x = 62
    for badge in badges:
        width = stringWidth(badge, "Helvetica-Bold", 11) + 24
        pdf.setFillColor(HexColor("#1B3859"))
        pdf.roundRect(x, 78, width, 27, 13, stroke=0, fill=1)
        pdf.setFont("Helvetica-Bold", 11)
        set_fill(pdf, WHITE)
        pdf.drawCentredString(x + width / 2, 87, badge)
        x += width + 10
    footer(pdf, 1, dark=True)
    pdf.showPage()


def slide_2(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    title(pdf, "01 - Problem and approach", "Risk intelligence breaks at the handoff")
    rounded_card(pdf, 48, 90, 400, 330)
    pdf.setFont("Helvetica-Bold", 18)
    set_fill(pdf, RED)
    pdf.drawString(75, 380, "THE GAP")
    draw_bullets(
        pdf,
        [
            "News and social posts arrive in incompatible formats and repeat the same event.",
            "A sentiment label alone does not describe event type, severity, confidence, "
            "or exposure.",
            "Manual handoffs make the path from narrative to portfolio impact slow and hard "
            "to audit.",
        ],
        75,
        335,
        330,
        size=16,
    )
    rounded_card(pdf, 478, 90, 434, 330, fill=HexColor("#EAF8F7"), stroke=TEAL)
    pdf.setFont("Helvetica-Bold", 18)
    set_fill(pdf, TEAL)
    pdf.drawString(505, 380, "THE IMPACTTRAIL APPROACH")
    steps = [
        ("1", "Normalize", "News + social + replay"),
        ("2", "Understand", "Entity + sentiment + event"),
        ("3", "Score", "Impact + confidence + evidence"),
        ("4", "Act", "Automatic, idempotent stress test"),
    ]
    for index, (number, name, description) in enumerate(steps):
        y = 320 - index * 66
        pdf.setFillColor(INK)
        pdf.circle(525, y + 6, 15, stroke=0, fill=1)
        pdf.setFont("Helvetica-Bold", 12)
        set_fill(pdf, WHITE)
        pdf.drawCentredString(525, y + 2, number)
        pdf.setFont("Helvetica-Bold", 15)
        set_fill(pdf, INK)
        pdf.drawString(554, y + 5, name)
        pdf.setFont("Helvetica", 12)
        set_fill(pdf, MUTED)
        pdf.drawString(665, y + 5, description)
    pdf.setFillColor(INK)
    pdf.roundRect(48, 45, 864, 28, 14, stroke=0, fill=1)
    pdf.setFont("Helvetica-Bold", 12)
    set_fill(pdf, WHITE)
    pdf.drawCentredString(
        WIDTH / 2,
        54,
        "Design goal: one traceable path from source evidence to portfolio loss drivers",
    )
    footer(pdf, 2)
    pdf.showPage()


def slide_3(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    image = ImageReader(str(DOCS / "architecture.png"))
    pdf.drawImage(image, 45, 42, width=870, height=489, preserveAspectRatio=True, mask="auto")
    footer(pdf, 3)
    pdf.showPage()


def slide_4(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    title(
        pdf,
        "03 - AI/NLP risk engine",
        "A signal is a contract, not a black-box label",
        "Required outputs are bounded and augmented with confidence, evidence, provenance, "
        "and versions.",
    )
    cards = [
        ("SENTIMENT", "-1.0 to +1.0", "P(positive) - P(negative)", TEAL),
        ("EVENT", "10-class taxonomy", "explicit other / abstention", BLUE),
        ("IMPACT", "1.0 to 10.0", "severity and urgency", GOLD),
    ]
    for index, (label, value, note, color) in enumerate(cards):
        x = 48 + index * 294
        rounded_card(pdf, x, 275, 270, 125)
        pdf.setFont("Helvetica-Bold", 11)
        set_fill(pdf, color)
        pdf.drawString(x + 20, 370, label)
        pdf.setFont("Helvetica-Bold", 23)
        set_fill(pdf, INK)
        pdf.drawString(x + 20, 333, value)
        pdf.setFont("Helvetica", 12)
        set_fill(pdf, MUTED)
        pdf.drawString(x + 20, 302, note)

    rounded_card(pdf, 48, 55, 520, 185, fill=INK, stroke=INK)
    pdf.setFont("Helvetica-Bold", 16)
    set_fill(pdf, WHITE)
    pdf.drawString(72, 204, "EXPLAINABLE IMPACT FORMULA")
    factors = [
        ("Event severity", "30%"),
        ("Entity relevance", "15%"),
        ("Corroboration", "15%"),
        ("Tone | confidence | novelty | source", "40%"),
    ]
    for index, (name, weight) in enumerate(factors):
        y = 170 - index * 32
        pdf.setFont("Helvetica", 12)
        set_fill(pdf, HexColor("#C8D6E5"))
        pdf.drawString(72, y, name)
        pdf.setFont("Helvetica-Bold", 12)
        set_fill(pdf, GOLD if index == 0 else TEAL)
        pdf.drawRightString(535, y, weight)

    rounded_card(pdf, 598, 55, 314, 185, fill=HexColor("#EAF8F7"), stroke=TEAL)
    pdf.setFont("Helvetica-Bold", 16)
    set_fill(pdf, INK)
    pdf.drawString(622, 204, "AUTOMATIC STRESS GATE")
    draw_bullets(
        pdf,
        [
            "Event confidence >= 0.65",
            "Impact confidence >= 0.60",
            "Impact strictly > 7.0",
            "Compatible scenario + idempotency",
        ],
        622,
        170,
        260,
        size=12,
    )
    footer(pdf, 4)
    pdf.showPage()


def slide_5(pdf: canvas.Canvas, stress: dict[str, Any] | None) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    pdf.setFont("Helvetica-Bold", 14)
    set_fill(pdf, TEAL)
    pdf.drawString(48, HEIGHT - 47, "04 - STRATEGIC PORTFOLIO STRESS TESTING")
    pdf.setFont("Helvetica-Bold", 26)
    set_fill(pdf, INK)
    pdf.drawString(48, HEIGHT - 100, "High-impact credit signal to explainable portfolio loss")
    draw_wrapped(
        pdf,
        "Illustrative valuation across loans, bonds, and derivatives; every position reconciles.",
        48,
        HEIGHT - 124,
        WIDTH - 96,
        size=13,
        color=MUTED,
    )
    if not stress:
        draw_wrapped(pdf, "Run make demo before generating the deck.", 48, 300, 800, 24, color=RED)
        footer(pdf, 5)
        pdf.showPage()
        return
    metric_card(
        pdf, 48, 285, 200, "Pre-stress value", f"${stress['pre_stress_value'] / 1e6:.1f}M", BLUE
    )
    metric_card(
        pdf, 270, 285, 200, "Post-stress value", f"${stress['post_stress_value'] / 1e6:.1f}M", TEAL
    )
    metric_card(pdf, 492, 285, 200, "Scenario P&L", f"-${abs(stress['pnl']) / 1e6:.1f}M", RED)
    metric_card(pdf, 714, 285, 198, "Portfolio loss", f"{stress['pnl_percent']:.2%}", GOLD)

    rounded_card(pdf, 48, 55, 415, 195)
    pdf.setFont("Helvetica-Bold", 16)
    set_fill(pdf, INK)
    pdf.drawString(72, 218, stress["scenario_name"].upper())
    draw_wrapped(pdf, stress["scenario_description"], 72, 192, 360, size=13, color=MUTED)
    pdf.setFont("Helvetica-Bold", 10)
    set_fill(pdf, RED)
    pdf.drawString(
        72,
        160,
        f"TRIGGER {stress['trigger_impact']:.1f}/10  |  "
        f"{len(stress['position_results'])} POSITIONS  |  "
        f"${abs(stress['reconciliation_error']):,.2f} RECONCILIATION",
    )
    shocks = stress["base_shocks"]
    shock_lines = [
        f"Equity: {shocks['equity_pct']:.0%}",
        f"Rates: +{shocks['rates_bps']:.0f} bps",
        f"Credit spread: +{shocks['credit_spread_bps']:.0f} bps",
        f"PD multiplier: {shocks['pd_multiplier']:.2f}x",
    ]
    pdf.setFont("Helvetica-Bold", 12)
    set_fill(pdf, INK)
    for index, line in enumerate(shock_lines):
        pdf.drawString(72 + (index % 2) * 180, 118 - (index // 2) * 32, line)

    rounded_card(pdf, 490, 55, 422, 195, fill=INK, stroke=INK)
    pdf.setFont("Helvetica-Bold", 16)
    set_fill(pdf, WHITE)
    pdf.drawString(514, 218, "VALUATION CHANNELS")
    channels = [
        ("LOANS", "change in EAD x PD x LGD"),
        ("BONDS", "duration + convexity + spread"),
        ("DERIVATIVES", "delta / DV01 / FX sensitivity"),
    ]
    for index, (name, method) in enumerate(channels):
        y = 174 - index * 46
        pdf.setFont("Helvetica-Bold", 12)
        set_fill(pdf, GOLD if index == 1 else TEAL)
        pdf.drawString(514, y, name)
        pdf.setFont("Helvetica", 12)
        set_fill(pdf, HexColor("#C8D6E5"))
        pdf.drawString(630, y, method)
    pdf.setFont("Helvetica-Bold", 10)
    set_fill(pdf, HexColor("#A9BED3"))
    pdf.drawString(514, 64, "ALL POSITION RESULTS RECONCILE TO PORTFOLIO TOTALS")
    footer(pdf, 5)
    pdf.showPage()


def slide_6(pdf: canvas.Canvas, metrics: dict[str, Any], evaluation: dict[str, Any]) -> None:
    pdf.setFillColor(PAPER)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    title(
        pdf,
        "05 - Measured results",
        "Reproducible evidence, with the limitations attached",
        "Replay proves the workflow; compact synthetic sets verify contracts, not production "
        "generalization.",
    )
    preview = ImageReader(str(DOCS / "dashboard_preview.png"))
    pdf.drawImage(preview, 465, 74, width=447, height=251, preserveAspectRatio=True, mask="auto")
    replay = metrics["replay_summary"]
    top_metrics = [
        ("Inputs / unique", f"{replay['fetched']} / {metrics['documents']}", TEAL),
        ("Exact duplicates", str(replay["duplicates"]), BLUE),
        ("Stress runs", str(metrics["stress_runs"]), GOLD),
        ("Replay failures", str(replay["failed"]), RED),
    ]
    for index, (label_text, value, color) in enumerate(top_metrics):
        metric_card(pdf, 48 + index * 219, 336, 207, label_text, value, color)
    rounded_card(pdf, 48, 74, 394, 235)
    pdf.setFont("Helvetica-Bold", 16)
    set_fill(pdf, INK)
    pdf.drawString(72, 270, "SYNTHETIC-SET CONTRACT EVIDENCE")
    rows = [
        (
            "Finance sentiment",
            str(evaluation["sentiment"]["samples"]),
            f"{evaluation['sentiment']['macro_f1']:.0%} F1",
        ),
        (
            "Event taxonomy",
            str(evaluation["event"]["samples"]),
            f"{evaluation['event']['macro_f1']:.0%} F1",
        ),
        (
            "Impact severity",
            str(evaluation["impact"]["samples"]),
            f"{evaluation['impact']['mae']:.2f} MAE",
        ),
    ]
    pdf.setFont("Helvetica-Bold", 10)
    set_fill(pdf, MUTED)
    pdf.drawString(72, 230, "BASELINE")
    pdf.drawString(260, 230, "N")
    pdf.drawString(315, 230, "RESULT")
    for index, (name, count, score) in enumerate(rows):
        y = 196 - index * 39
        pdf.setStrokeColor(LINE)
        pdf.line(72, y - 10, 415, y - 10)
        pdf.setFont("Helvetica", 12)
        set_fill(pdf, INK)
        pdf.drawString(72, y, name)
        pdf.drawString(260, y, count)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(315, y, score)
    pdf.setFont("Helvetica", 10)
    set_fill(pdf, RED)
    pdf.drawString(72, 87, "Synthetic rubric data - not a production accuracy claim")
    footer(pdf, 6)
    pdf.showPage()


def slide_7(pdf: canvas.Canvas) -> None:
    pdf.setFillColor(INK)
    pdf.rect(0, 0, WIDTH, HEIGHT, stroke=0, fill=1)
    pdf.setFont("Helvetica-Bold", 14)
    set_fill(pdf, GOLD)
    pdf.drawString(48, HEIGHT - 50, "06 - DOMAIN IMPACT AND RESPONSIBLE SCALE")
    pdf.setFont("Helvetica-Bold", 32)
    set_fill(pdf, WHITE)
    pdf.drawString(48, HEIGHT - 92, "Make every automated risk action challengeable")
    rounded_card(pdf, 48, 118, 400, 310, fill=HexColor("#173354"), stroke=HexColor("#274B70"))
    pdf.setFont("Helvetica-Bold", 17)
    set_fill(pdf, TEAL)
    pdf.drawString(74, 388, "ANALYST VALUE")
    analyst_value = [
        "Prioritize narratives by severity and exposed portfolio drivers.",
        "Replace manual handoffs with one source-to-loss decision trace.",
        "Apply consistent confidence and scenario policy gates.",
        "Challenge every score through evidence, factors, and assumptions.",
    ]
    for index, item in enumerate(analyst_value):
        y = 342 - index * 57
        draw_wrapped(pdf, f"- {item}", 74, y, 340, size=14, color=HexColor("#DCE7F2"))

    rounded_card(pdf, 478, 118, 434, 310, fill=HexColor("#173354"), stroke=HexColor("#274B70"))
    pdf.setFont("Helvetica-Bold", 17)
    set_fill(pdf, GOLD)
    pdf.drawString(504, 388, "RESPONSIBLE SCALE")
    responsible_scale = [
        "Keep human review; no trading, credit, or regulatory-capital claim.",
        "Validate on larger independently reviewed, time-split public data.",
        "Add semantic clustering, calibration, drift, and analyst feedback.",
        "Promote infrastructure only when measured volume requires it.",
    ]
    for index, item in enumerate(responsible_scale):
        y = 342 - index * 57
        draw_wrapped(pdf, f"- {item}", 504, y, 374, size=14, color=HexColor("#DCE7F2"))
    pdf.setFont("Helvetica-Bold", 20)
    set_fill(pdf, WHITE)
    pdf.drawString(48, 78, "ImpactTrail: evidence -> policy -> scenario -> portfolio decision")
    footer(pdf, 7, dark=True)
    pdf.showPage()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    metrics, stress = load_results()
    evaluation = load_evaluation()
    pdf = canvas.Canvas(str(CANONICAL), pagesize=PAGE_SIZE, pageCompression=1)
    pdf.setTitle("ImpactTrail - S&P Global & Crisil Campus Hackathon 2026")
    pdf.setAuthor(os.getenv("IMPACTTRAIL_CANDIDATE_NAME", "Alok Chandra"))
    pdf.setSubject("AI/NLP financial risk engine and strategic portfolio stress testing")
    slide_1(pdf, metrics)
    slide_2(pdf)
    slide_3(pdf)
    slide_4(pdf)
    slide_5(pdf, stress)
    slide_6(pdf, metrics, evaluation)
    slide_7(pdf)
    pdf.save()
    shutil.copy2(CANONICAL, REPO_COPY)
    print(f"Created {CANONICAL}")
    print(f"Mirrored repository deliverable to {REPO_COPY}")


if __name__ == "__main__":
    main()
