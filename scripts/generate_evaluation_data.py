from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/evaluation"

ENTITIES = [
    "Nova Bank",
    "Aeon Technologies",
    "Orion Pharma",
    "Cedar Logistics",
    "Atlas Motors",
    "Vertex Telecom",
    "Meridian Retail",
    "Lumen Aerospace",
    "Terra Mining",
    "Helios Energy",
]

SENTIMENT_CONTEXTS = [
    "in its latest market update",
    "for the current reporting period",
    "during the annual business review",
]

SENTIMENT_TEMPLATES = {
    "positive": [
        "{entity} reports strong revenue growth {context}",
        "{entity} records a profit beat {context}",
        "{entity} is upgraded after resilient demand {context}",
        "{entity} raises guidance following record orders {context}",
        "{entity} gains market share with strong execution {context}",
        "{entity} receives approval for an approved expansion {context}",
        "{entity} reports a surge in profit {context}",
        "{entity} beats forecasts as growth accelerates {context}",
        "{entity} remains resilient and records a gain {context}",
        "{entity} announces a successful launch and strong demand {context}",
    ],
    "neutral": [
        "{entity} publishes its annual meeting calendar {context}",
        "{entity} schedules an investor briefing {context}",
        "{entity} appoints a non-executive director {context}",
        "{entity} files a routine corporate disclosure {context}",
        "{entity} confirms operations continue at current levels {context}",
        "{entity} updates its governance policy {context}",
        "{entity} completes planned maintenance {context}",
        "{entity} announces participation in an industry conference {context}",
        "{entity} publishes a standard shareholder notice {context}",
        "{entity} holds its scheduled community meeting {context}",
    ],
    "negative": [
        "{entity} is downgraded after a missed payment {context}",
        "{entity} reports a ransomware breach and outage {context}",
        "{entity} issues a profit warning after a revenue decline {context}",
        "{entity} faces sanctions and a liquidity crisis {context}",
        "{entity} records a loss as demand plunges {context}",
        "{entity} enters bankruptcy after a default {context}",
        "{entity} faces an investigation and a large fine {context}",
        "{entity} announces a recall after a safety breach {context}",
        "{entity} misses forecasts as inflation pressures margins {context}",
        "{entity} suffers a cyber breach and operational outage {context}",
    ],
}

# Ten examples per class provide balanced coverage of every required and extended event label.
# Impact targets are expert-specified severity/urgency rubric values, not realized market returns.
EVENT_CASES: dict[str, list[tuple[str, float, str]]] = {
    "geopolitical": [
        ("Government imposes sanctions after a border conflict", 8.4, "single_cue"),
        ("Export ban follows escalating regional conflict", 8.2, "single_cue"),
        ("Trade restriction disrupts critical supply routes", 7.6, "paraphrase"),
        ("War closes a major cross-border transport corridor", 9.3, "high_severity"),
        ("Naval blockade delays energy shipments", 8.7, "paraphrase"),
        ("New sanctions restrict access to international funding", 8.5, "finance_context"),
        ("Border conflict forces factories to suspend deliveries", 8.8, "operational_context"),
        ("Invasion triggers an export ban on strategic materials", 9.5, "multi_cue"),
        ("Trade restrictions intensify after diplomatic conflict", 8.0, "multi_cue"),
        ("Regional war raises commodity and shipping risk", 9.1, "high_severity"),
    ],
    "macroeconomic": [
        ("Central bank announces a rate hike as inflation accelerates", 7.8, "multi_cue"),
        ("GDP contracts as recession risk increases", 8.0, "multi_cue"),
        ("Unemployment rises during a broad economic slowdown", 6.9, "single_cue"),
        ("Monetary policy remains restrictive amid persistent inflation", 7.4, "paraphrase"),
        ("Central bank signals another rate hike", 7.2, "single_cue"),
        ("Recession fears deepen after weak GDP data", 8.1, "multi_cue"),
        ("Rate cut is announced as economic growth weakens", 6.8, "direction_case"),
        ("Inflation reaches a new high and unemployment increases", 7.7, "multi_cue"),
        ("Monetary policy tightening pressures credit conditions", 7.3, "finance_context"),
        ("Central bank rate hike follows an inflation surprise", 7.9, "multi_cue"),
    ],
    "credit_event": [
        ("{entity} misses payment and enters restructuring talks", 9.2, "multi_cue"),
        ("{entity} defaults after a severe liquidity crisis", 9.6, "high_severity"),
        ("{entity} is downgraded following a covenant breach", 8.5, "multi_cue"),
        ("{entity} files for bankruptcy after missed payment", 9.7, "high_severity"),
        ("{entity} faces insolvency as funding expires", 9.3, "single_cue"),
        ("{entity} begins debt restructuring after a downgrade", 8.8, "multi_cue"),
        ("{entity} warns of a liquidity crisis", 8.7, "single_cue"),
        ("{entity} breaches a covenant and misses payment", 9.0, "multi_cue"),
        ("{entity} default follows an abrupt funding withdrawal", 9.4, "high_severity"),
        ("{entity} receives a downgrade but remains current on payments", 7.1, "low_severity"),
    ],
    "merger_acquisition": [
        ("{entity} announces an acquisition of a regional competitor", 5.7, "single_cue"),
        ("Board approves a proposed merger", 5.6, "single_cue"),
        ("{entity} receives a takeover offer", 6.0, "single_cue"),
        ("{entity} agrees to acquire a technology supplier", 5.8, "single_cue"),
        ("Shareholders approve a strategic buyout", 6.1, "single_cue"),
        ("{entity} begins a divestiture of non-core assets", 5.2, "single_cue"),
        ("A tender offer is launched for {entity}", 6.3, "single_cue"),
        ("Regulators review the proposed merger", 6.6, "competing_cue"),
        ("{entity} completes an acquisition after board approval", 5.4, "single_cue"),
        ("A cross-border takeover of {entity} is announced", 6.4, "paraphrase"),
    ],
    "product_launch": [
        ("{entity} launches an approved digital platform", 4.5, "positive_case"),
        ("{entity} schedules a product release", 4.1, "single_cue"),
        ("{entity} unveils a new analytics service", 4.3, "single_cue"),
        ("{entity} begins a nationwide product rollout", 4.8, "single_cue"),
        ("{entity} receives approval for a new medicine", 5.1, "positive_case"),
        ("{entity} delays a product launch", 5.9, "negative_case"),
        ("{entity} announces a product delay after testing", 6.0, "negative_case"),
        ("{entity} recalls a recently launched device", 6.8, "negative_case"),
        ("{entity} launches a service after regulatory approval", 4.9, "competing_cue"),
        ("{entity} expands the rollout of its approved product", 4.6, "positive_case"),
    ],
    "regulatory_legal": [
        ("Regulator opens an antitrust investigation into {entity}", 7.5, "multi_cue"),
        ("Court imposes a large penalty on {entity}", 7.6, "single_cue"),
        ("{entity} faces an enforcement action", 7.2, "single_cue"),
        ("A lawsuit alleges misconduct by {entity}", 6.8, "single_cue"),
        ("Regulation requires {entity} to change its controls", 6.4, "single_cue"),
        ("{entity} receives a fine after an investigation", 7.4, "multi_cue"),
        ("Competition regulator begins an antitrust review", 7.0, "multi_cue"),
        ("Court penalty follows a lengthy lawsuit", 7.3, "multi_cue"),
        ("{entity} settles an enforcement investigation", 6.9, "multi_cue"),
        ("New regulation restricts a key product line", 7.1, "single_cue"),
    ],
    "operational_cyber": [
        ("{entity} suffers a ransomware breach", 8.5, "multi_cue"),
        ("Network outage causes a major operational disruption", 7.6, "multi_cue"),
        ("Cyberattack shuts down {entity} systems", 8.7, "multi_cue"),
        ("{entity} reports a data breach", 7.4, "single_cue"),
        ("Plant shutdown interrupts production", 7.3, "single_cue"),
        ("Payment outage affects {entity} customers", 7.1, "single_cue"),
        ("Internal fraud causes an operational disruption", 7.7, "multi_cue"),
        ("Ransomware attack leads to a week-long outage", 8.9, "multi_cue"),
        ("Cyber attack disrupts a critical service", 8.2, "multi_cue"),
        ("{entity} restores systems after a brief outage", 6.2, "low_severity"),
    ],
    "earnings_guidance": [
        ("{entity} raises guidance after record quarterly earnings", 5.1, "positive_case"),
        ("{entity} issues a profit warning", 6.8, "negative_case"),
        ("Revenue falls below the company forecast", 6.0, "negative_case"),
        ("{entity} reports quarterly results in line with expectations", 4.2, "neutral_case"),
        ("Margin improves as revenue grows", 4.8, "positive_case"),
        ("{entity} lowers guidance after weak earnings", 6.4, "negative_case"),
        ("Forecast is unchanged after quarterly results", 4.0, "neutral_case"),
        ("{entity} reports record revenue and profit", 4.9, "positive_case"),
        ("Earnings miss prompts a lower forecast", 6.3, "negative_case"),
        ("{entity} expects stable margin in the next quarter", 4.1, "neutral_case"),
    ],
    "climate_natural_hazard": [
        ("Severe flood closes a regional manufacturing facility", 7.7, "single_cue"),
        ("Wildfire disrupts mining operations", 7.5, "single_cue"),
        ("Hurricane damages a coastal logistics hub", 8.3, "single_cue"),
        ("Earthquake forces factories to stop production", 8.8, "single_cue"),
        ("Drought reduces output across the region", 7.2, "single_cue"),
        ("Cyclone interrupts shipping and power supply", 8.1, "single_cue"),
        ("Natural disaster damages critical infrastructure", 8.5, "single_cue"),
        ("Flood and wildfire affect separate operating sites", 8.4, "multi_cue"),
        ("Drought causes a temporary production slowdown", 6.8, "low_severity"),
        ("Hurricane warning prompts precautionary closures", 7.0, "low_severity"),
    ],
    "other": [
        ("{entity} schedules a community meeting", 2.0, "routine"),
        ("Executive speaks at an industry conference", 2.2, "routine"),
        ("{entity} publishes its annual calendar", 1.9, "routine"),
        ("Board appoints a non-executive director", 2.4, "routine"),
        ("{entity} opens a routine investor briefing", 2.1, "routine"),
        ("Company updates its corporate website", 1.6, "routine"),
        ("{entity} issues a standard governance notice", 2.0, "routine"),
        ("Management attends a scheduled trade event", 2.3, "routine"),
        ("{entity} confirms its next annual meeting date", 1.8, "routine"),
        ("Company publishes a general information bulletin", 1.7, "routine"),
    ],
}


def write_sentiment() -> None:
    rows: list[dict[str, str]] = []
    row_number = 0
    for label, templates in SENTIMENT_TEMPLATES.items():
        for context_index, context in enumerate(SENTIMENT_CONTEXTS):
            for template_index, template in enumerate(templates):
                entity = ENTITIES[(template_index + context_index) % len(ENTITIES)]
                row_number += 1
                rows.append(
                    {
                        "example_id": f"sent-{row_number:03d}",
                        "text": template.format(entity=entity, context=context),
                        "label": label,
                        "slice": "base" if context_index == 0 else "paraphrase",
                    }
                )
    path = OUTPUT / "sentiment_gold.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_events() -> None:
    rows: list[dict[str, str | float]] = []
    row_number = 0
    for label, cases in EVENT_CASES.items():
        for case_index, (template, impact, challenge_type) in enumerate(cases):
            row_number += 1
            entity = ENTITIES[case_index % len(ENTITIES)]
            rows.append(
                {
                    "example_id": f"event-{row_number:03d}",
                    "text": template.format(entity=entity),
                    "label": label,
                    "impact_score": f"{impact:.1f}",
                    "challenge_type": challenge_type,
                }
            )
    path = OUTPUT / "events_gold.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_sentiment()
    write_events()
    print("Generated 90 sentiment and 100 event/impact evaluation examples.")


if __name__ == "__main__":
    main()
