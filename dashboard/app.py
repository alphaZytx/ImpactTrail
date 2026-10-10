from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_URL = os.getenv("IMPACTTRAIL_API_URL", "http://127.0.0.1:8000")
IMPACT_WEIGHTS = {
    "event_severity": 0.30,
    "entity_relevance": 0.15,
    "sentiment_intensity": 0.10,
    "model_confidence": 0.10,
    "corroboration": 0.15,
    "novelty": 0.10,
    "source_quality": 0.10,
}

st.set_page_config(
    page_title="ImpactTrail | Financial Risk Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#10233f; --teal:#16a6a1; --gold:#f4b942; --paper:#f5f7fb; }
    .stApp { background: linear-gradient(180deg,#f8fafc 0%,#eef3f8 100%); }
    .block-container { padding-top:2.25rem; padding-bottom:2rem; }
    [data-testid="stToolbar"], #MainMenu { visibility:hidden; }
    [data-testid="stSidebar"] { background:#10233f; color:white; }
    [data-testid="stSidebar"] * { color:white; }
    [data-testid="stSidebar"] button[kind="secondary"] {
      background:#1b3859; border-color:#365779; }
    [data-testid="stSidebar"] button[kind="secondary"] * { color:white !important; }
    .hero { padding:1.2rem 1.4rem; border-radius:18px; color:white;
      background:linear-gradient(118deg,#10233f 0%,#17506a 58%,#16a6a1 100%);
      box-shadow:0 12px 32px rgba(16,35,63,.16); margin-bottom:1rem; }
    .hero h1 { margin:0; font-size:2.15rem; letter-spacing:-.03em; }
    .hero p { margin:.35rem 0 0; opacity:.88; }
    .pill { display:inline-block; padding:.2rem .55rem; border-radius:999px;
      background:rgba(255,255,255,.16); margin-right:.35rem; font-size:.78rem; }
    .notice { border-left:4px solid #f4b942; background:#fff8e8; color:#5d4510;
      padding:.65rem .9rem; border-radius:6px; }
    div[data-testid="stMetric"] { background:white; border:1px solid #e2e8f0;
      padding:.8rem 1rem; border-radius:14px; box-shadow:0 4px 14px rgba(16,35,63,.05); }
    .signal-card { background:white; border:1px solid #dde5ef; border-radius:14px;
      padding:.8rem 1rem; margin:.45rem 0; }
    .replay-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
      gap:.45rem; margin:.65rem 0 1rem; }
    .replay-grid div { background:#f8fafc; border:1px solid #d8e1ec; border-radius:10px;
      color:#10233f !important; padding:.45rem .6rem; }
    .replay-grid span { color:#60758f !important; display:block; font-size:.7rem;
      letter-spacing:.04em; text-transform:uppercase; }
    .replay-grid b { color:#10233f !important; font-size:1.15rem; }
    .trace-kicker { color:#16a6a1; font-size:.78rem; font-weight:700;
      letter-spacing:.08em; text-transform:uppercase; margin-bottom:.25rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=3, show_spinner=False)
def api_get(api_url: str, path: str) -> Any:
    with httpx.Client(timeout=8.0) as client:
        response = client.get(f"{api_url}{path}")
        response.raise_for_status()
        return response.json()


def api_post(api_url: str, path: str, payload: dict[str, Any]) -> Any:
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{api_url}{path}", json=payload)
        response.raise_for_status()
        api_get.clear()
        return response.json()


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:,.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:,.2f}M"
    return f"{sign}${value:,.0f}"


def label(value: str) -> str:
    return value.replace("_", " ").title()


def format_timestamp(value: str) -> str:
    timestamp = pd.to_datetime(value, utc=True)
    return timestamp.strftime("%d %b %Y · %H:%M UTC")


def format_shock(name: str, value: float) -> str:
    if name in {"equity_pct", "fx_pct"}:
        return f"{value:+.1%}"
    if name in {"rates_bps", "credit_spread_bps"}:
        return f"{value:+,.0f} bps"
    if name == "pd_multiplier":
        return f"{value:.2f}x"
    return f"{value:,.2f}"


def signal_name(signal: dict[str, Any]) -> str:
    return (
        f"{signal['entity']['name']} · {label(signal['event']['label'])} · "
        f"{signal['impact']['score']:.1f}/10"
    )


def render_replay_summary(summary: dict[str, Any]) -> None:
    values = [
        ("Fetched", summary["fetched"]),
        ("Processed", summary["processed"]),
        ("Duplicates", summary["duplicates"]),
        ("Signals", summary["signals"]),
        ("Stress runs", summary["stress_runs"]),
        ("Failed", summary["failed"]),
    ]
    cards = "".join(f"<div><span>{name}</span><b>{value}</b></div>" for name, value in values)
    st.markdown(f'<div class="replay-grid">{cards}</div>', unsafe_allow_html=True)


with st.sidebar:
    st.markdown("## ◈ ImpactTrail")
    st.caption("Financial risk intelligence")
    with st.expander("Advanced"):
        api_url = st.text_input("API URL", DEFAULT_API_URL)
        st.caption("Change only when the API runs on a different host or port.")
    if st.button("Reset & run demo replay", type="primary", width="stretch"):
        try:
            result = api_post(
                api_url,
                "/api/v1/replays",
                {"fixture": "data/demo/mixed_source_events.jsonl", "reset": True},
            )
            st.session_state["replay_summary"] = result
            st.success("Demo state rebuilt from the deterministic fixture.")
        except Exception as exc:
            st.error(f"Replay failed: {exc}")
    replay_summary = st.session_state.get("replay_summary")
    if replay_summary:
        render_replay_summary(replay_summary)
    else:
        st.caption("Reset-and-replay rebuilds the same auditable demo state every time.")
    if st.button("Refresh", width="stretch"):
        api_get.clear()
        st.rerun()
    st.divider()
    st.markdown("**Mode**  ")
    st.caption("Deterministic replay ready")
    st.markdown("**Important**")
    st.caption("Educational prototype. Not investment advice or regulatory stress testing.")

st.markdown(
    """
    <div class="hero">
      <span class="pill">NEWS + SOCIAL</span><span class="pill">AUDITABLE AI</span>
      <span class="pill">STRESS TESTING</span>
      <h1>From narrative noise to portfolio impact.</h1>
      <p>Entity-aware sentiment, event severity, and transparent stress scenarios
      in one workflow.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    health = api_get(api_url, "/readyz")
    metrics = api_get(api_url, "/api/v1/metrics/summary")
    signal_payload = api_get(api_url, "/api/v1/signals?limit=500")
    signals: list[dict[str, Any]] = signal_payload["items"]
    stress_runs: list[dict[str, Any]] = api_get(api_url, "/api/v1/stress-tests?limit=100")
    portfolio = api_get(api_url, "/api/v1/portfolio/summary")
except Exception as exc:
    st.error("ImpactTrail API is not ready.")
    st.code("make demo\nmake api\n# In another terminal:\nmake dashboard", language="bash")
    st.caption(str(exc))
    st.stop()

decision_policy: dict[str, Any] = metrics["decision_policy"]
priority_signals = sorted(
    signals,
    key=lambda item: (item["impact"]["score"], item["published_at"]),
    reverse=True,
)
priority_stress_runs = sorted(
    stress_runs,
    key=lambda item: (item["trigger_impact"], abs(item["pnl"])),
    reverse=True,
)

overview_tab, trace_tab, signal_tab, stress_tab, portfolio_tab, quality_tab = st.tabs(
    [
        "Overview",
        "Decision trace",
        "Signal explorer",
        "Stress lab",
        "Portfolio",
        "Validation & controls",
    ]
)

with overview_tab:
    columns = st.columns(5)
    columns[0].metric("Documents", metrics["documents"])
    columns[1].metric("Signals", metrics["signals"])
    columns[2].metric("Confidence-qualified", metrics["actionable_signals"])
    columns[3].metric("Stress runs", metrics["stress_runs"])
    priority_loss = priority_stress_runs[0]["pnl"] if priority_stress_runs else 0
    columns[4].metric("Priority stressed P&L", money(priority_loss))

    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Priority risk signals")
        if not priority_signals:
            st.info("Run the deterministic replay to populate the engine.")
        for signal in priority_signals[:5]:
            impact = signal["impact"]["score"]
            status_label = "QUALIFIED" if signal["actionable"] else "MONITOR"
            entity_name = escape(str(signal["entity"]["name"]))
            event_name = escape(label(str(signal["event"]["label"])))
            source_name = escape(str(signal["source"]["name"]))
            st.markdown(
                f"""<div class="signal-card"><b>{entity_name}</b> · {status_label}<br>
                <span style="color:#50647f">{event_name} ·
                impact {impact:.1f}/10 · sentiment {signal["sentiment"]["score"]:+.2f} ·
                {source_name}</span></div>""",
                unsafe_allow_html=True,
            )
    with right:
        st.subheader("Impact distribution")
        if signals:
            chart_df = pd.DataFrame(
                {
                    "event": [item["event"]["label"].replace("_", " ").title() for item in signals],
                    "impact": [item["impact"]["score"] for item in signals],
                    "entity": [item["entity"]["name"] for item in signals],
                }
            )
            figure = px.scatter(
                chart_df,
                x="impact",
                y="event",
                color="impact",
                hover_name="entity",
                color_continuous_scale=["#4e79a7", "#f4b942", "#c63d4f"],
                range_color=[1, 10],
            )
            figure.update_layout(
                height=340, margin=dict(l=0, r=0, t=10, b=0), coloraxis_showscale=False
            )
            figure.add_vline(
                x=decision_policy["stress_impact_strictly_above"],
                line_dash="dash",
                line_color="#c63d4f",
                annotation_text="Stress gate",
                annotation_position="top left",
            )
            st.plotly_chart(figure, width="stretch")

    st.markdown(
        '<div class="notice"><b>Interpretation:</b> impact measures estimated '
        "severity and urgency, "
        "not a predicted return. Confidence gates control automatic portfolio actions.</div>",
        unsafe_allow_html=True,
    )

with trace_tab:
    st.subheader("Decision trace")
    st.caption(
        "Follow one priority narrative from corroborating evidence through policy gates to "
        "portfolio loss."
    )
    if not priority_signals:
        st.info("Run the deterministic replay to populate the decision trace.")
    else:
        priority_by_id = {item["signal_id"]: item for item in priority_signals}
        trace_signal_id = st.selectbox(
            "Trace priority signal",
            options=list(priority_by_id),
            format_func=lambda signal_id: signal_name(priority_by_id[signal_id]),
            key="trace_signal_id",
        )
        trace_signal = priority_by_id[trace_signal_id]
        cluster_id = trace_signal["event_cluster_id"]
        cluster_signals = sorted(
            [item for item in signals if item["event_cluster_id"] == cluster_id],
            key=lambda item: item["published_at"],
        )
        linked_run = next(
            (item for item in priority_stress_runs if item["event_cluster_id"] == cluster_id),
            None,
        )

        st.markdown(
            '<div class="trace-kicker">1 · Clustered source evidence</div>', unsafe_allow_html=True
        )
        source_names = sorted({item["source"]["name"] for item in cluster_signals})
        st.markdown(
            f"**{len(cluster_signals)} records · {len(source_names)} independent source "
            f"{'type' if len(source_names) == 1 else 'types'} · one event cluster**"
        )
        evidence_columns = st.columns(min(2, len(cluster_signals)))
        for index, evidence in enumerate(cluster_signals):
            with evidence_columns[index % len(evidence_columns)], st.container(border=True):
                st.markdown(
                    f"**{evidence['source']['name'].upper()} · "
                    f"{label(evidence['source']['type'])}**"
                )
                st.write(f"“{evidence['explanation']['evidence_excerpt']}”")
                st.caption(
                    f"{format_timestamp(evidence['published_at'])} · {evidence['document_id']}"
                )

        st.markdown(
            '<div class="trace-kicker">2 · Structured risk signal</div>', unsafe_allow_html=True
        )
        signal_columns = st.columns(4)
        signal_columns[0].metric("Entity", trace_signal["entity"]["name"])
        signal_columns[0].caption(
            trace_signal["entity"].get("ticker")
            or trace_signal["entity"].get("sector")
            or "Resolved"
        )
        signal_columns[1].metric("Event", label(trace_signal["event"]["label"]))
        signal_columns[1].caption(
            f"{trace_signal['event']['confidence']:.0%} classification confidence"
        )
        signal_columns[2].metric(
            "Sentiment",
            f"{trace_signal['sentiment']['score']:+.2f}",
            trace_signal["sentiment"]["label"],
        )
        signal_columns[3].metric("Impact", f"{trace_signal['impact']['score']:.1f}/10")
        signal_columns[3].caption(f"{trace_signal['impact']['confidence']:.0%} impact confidence")

        event_confidence_min = float(decision_policy["event_confidence_min"])
        impact_confidence_min = float(decision_policy["impact_confidence_min"])
        stress_threshold = float(decision_policy["stress_impact_strictly_above"])
        supported_scenarios = set(decision_policy["supported_scenarios"])
        event_label = trace_signal["event"]["label"]
        matched_terms = {term.casefold() for term in trace_signal["event"]["matched_terms"]}
        exclusions = {
            term.casefold()
            for term in decision_policy.get("scenario_direction_exclusions", {}).get(
                event_label, []
            )
        }
        direction_supported = not (exclusions & matched_terms) or "rate hike" in matched_terms
        scenario_supported = event_label in supported_scenarios and direction_supported
        if event_label not in supported_scenarios:
            scenario_status = "not configured"
        elif not direction_supported:
            scenario_status = "direction held"
        else:
            scenario_status = "configured"
        gates = [
            (
                "Event confidence",
                event_label != "other"
                and trace_signal["event"]["confidence"] >= event_confidence_min,
                f"{trace_signal['event']['confidence']:.0%} ≥ {event_confidence_min:.0%}",
            ),
            (
                "Impact confidence",
                trace_signal["impact"]["confidence"] >= impact_confidence_min,
                f"{trace_signal['impact']['confidence']:.0%} ≥ {impact_confidence_min:.0%}",
            ),
            (
                "Impact severity",
                trace_signal["impact"]["score"] > stress_threshold,
                f"{trace_signal['impact']['score']:.1f} > {stress_threshold:.1f}",
            ),
            (
                "Compatible scenario",
                scenario_supported,
                f"{label(event_label)} {scenario_status}",
            ),
        ]
        st.markdown('<div class="trace-kicker">3 · Decision policy</div>', unsafe_allow_html=True)
        gate_columns = st.columns(4)
        for column, (gate_name, passed, detail) in zip(gate_columns, gates, strict=True):
            with column, st.container(border=True):
                st.markdown(f"**{'✓ PASS' if passed else '— HOLD'}**")
                st.markdown(gate_name)
                st.caption(detail)

        if all(passed for _, passed, _ in gates) and linked_run:
            st.success("All four gates passed. One cluster-level stress run was executed.")
        elif all(passed for _, passed, _ in gates):
            st.warning("The signal passes policy, but no linked stress run was found.")
        else:
            st.info("The signal remains inspectable, but automatic stress testing is gated.")

        contribution_rows = []
        for factor, strength in trace_signal["impact"]["components"].items():
            weight = IMPACT_WEIGHTS.get(factor, 0.0)
            contribution_rows.append(
                {
                    "factor": label(factor),
                    "strength": strength,
                    "weight": weight,
                    "points": 9 * strength * weight,
                }
            )
        contribution_frame = pd.DataFrame(contribution_rows).sort_values("points")
        contribution_figure = px.bar(
            contribution_frame,
            x="points",
            y="factor",
            orientation="h",
            title="Weighted impact-score contribution",
            text="points",
            hover_data={"strength": ":.0%", "weight": ":.0%", "points": ":.2f"},
            color_discrete_sequence=["#16a6a1"],
        )
        contribution_figure.update_traces(
            texttemplate="%{x:.2f}", textposition="outside", cliponaxis=False
        )
        contribution_figure.update_layout(
            height=345,
            margin=dict(l=0, r=30, t=45, b=0),
            xaxis_title="Points above the 1.0 baseline",
            yaxis_title=None,
            showlegend=False,
        )
        st.plotly_chart(contribution_figure, width="stretch")
        weighted_points = contribution_frame["points"].sum()
        st.caption(
            f"Impact formula: 1.0 baseline + {weighted_points:.2f} weighted points = "
            f"{min(10.0, 1 + weighted_points):.1f}/10 after rounding."
        )

        st.markdown(
            '<div class="trace-kicker">4 · Portfolio consequence</div>', unsafe_allow_html=True
        )
        if linked_run:
            st.markdown(f"**{linked_run['scenario_name']}** — {linked_run['scenario_description']}")
            position_frame = pd.DataFrame(linked_run["position_results"])
            sector_losses = (
                position_frame.groupby("sector", as_index=False)["pnl"].sum().sort_values("pnl")
            )
            top_driver = sector_losses.iloc[0]
            consequence_columns = st.columns(4)
            consequence_columns[0].metric("Scenario P&L", money(linked_run["pnl"]))
            consequence_columns[1].metric("Portfolio loss", f"{linked_run['pnl_percent']:.2%}")
            consequence_columns[2].metric(
                "Top sector driver", top_driver["sector"], money(float(top_driver["pnl"]))
            )
            consequence_columns[3].metric(
                "Reconciliation", f"${abs(linked_run['reconciliation_error']):,.2f}"
            )
            st.caption(
                f"Triggered at impact {linked_run['trigger_impact']:.1f}/10. Later corroborating "
                "records enrich the cluster without duplicating the stress run."
            )
        else:
            st.info("No portfolio stress was created for this signal under the current policy.")

with signal_tab:
    st.subheader("Auditable signal explorer")
    if priority_signals:
        signal_rows = [
            {
                "signal_id": item["signal_id"],
                "time": item["published_at"],
                "entity": item["entity"]["name"],
                "source": item["source"]["name"],
                "event": item["event"]["label"],
                "event_confidence": item["event"]["confidence"],
                "sentiment": item["sentiment"]["score"],
                "impact": item["impact"]["score"],
                "impact_confidence": item["impact"]["confidence"],
                "qualified": item["actionable"],
            }
            for item in priority_signals
        ]
        frame = pd.DataFrame(signal_rows)
        st.dataframe(
            frame.drop(columns=["signal_id"]),
            width="stretch",
            hide_index=True,
            column_config={
                "impact": st.column_config.ProgressColumn(min_value=1, max_value=10, format="%.1f"),
                "sentiment": st.column_config.NumberColumn(format="%+.2f"),
            },
        )
        selection = st.selectbox(
            "Inspect signal",
            options=range(len(priority_signals)),
            format_func=lambda index: signal_name(priority_signals[index]),
        )
        selected = priority_signals[selection]
        a, b, c = st.columns(3)
        a.metric(
            "Sentiment", f"{selected['sentiment']['score']:+.2f}", selected["sentiment"]["label"]
        )
        b.metric("Event confidence", f"{selected['event']['confidence']:.0%}")
        c.metric("Impact confidence", f"{selected['impact']['confidence']:.0%}")
        st.markdown(f"**Evidence:** {selected['explanation']['evidence_excerpt']}")
        st.markdown("**Reason codes:** " + ", ".join(selected["explanation"]["reason_codes"]))
        if selected["explanation"]["warnings"]:
            st.warning(" ".join(selected["explanation"]["warnings"]))
        with st.expander("Lineage and score components"):
            st.json(selected)
        st.download_button(
            "Download selected signal JSON",
            data=json.dumps(selected, indent=2),
            file_name=f"impacttrail-signal-{selected['signal_id']}.json",
            mime="application/json",
        )

with stress_tab:
    st.subheader("Strategic portfolio stress lab")
    if not priority_stress_runs:
        st.info("No qualifying high-impact event has triggered a stress run yet.")
    else:
        selected_run_index = st.selectbox(
            "Stress run",
            options=range(len(priority_stress_runs)),
            format_func=lambda index: (
                f"{priority_stress_runs[index]['scenario_name']} · impact "
                f"{priority_stress_runs[index]['trigger_impact']:.1f}/10"
            ),
        )
        run = priority_stress_runs[selected_run_index]
        columns = st.columns(4)
        columns[0].metric("Pre-stress value", money(run["pre_stress_value"]))
        columns[1].metric("Post-stress value", money(run["post_stress_value"]))
        columns[2].metric("Stressed P&L", money(run["pnl"]), f"{run['pnl_percent']:.2%}")
        columns[3].metric("Impact trigger", f"{run['trigger_impact']:.1f}/10")
        st.markdown(f"**{run['scenario_name']}** — {run['scenario_description']}")
        shock_frame = pd.DataFrame(
            [
                {"Risk factor": label(key), "Base shock": format_shock(key, float(value))}
                for key, value in run["base_shocks"].items()
            ]
        )
        st.dataframe(shock_frame, width="stretch", hide_index=True)
        st.caption(
            f"Base shocks are scaled by {run['severity_multiplier']:.0%} signal severity and "
            "position-level exposure matching."
        )

        results = pd.DataFrame(run["position_results"])
        left, right = st.columns(2)
        with left:
            by_asset = results.groupby("asset_type", as_index=False)["pnl"].sum()
            figure = px.bar(
                by_asset,
                x="asset_type",
                y="pnl",
                title="Stressed P&L by asset class",
                color="pnl",
                color_continuous_scale=["#c63d4f", "#f4b942", "#16a6a1"],
            )
            figure.update_layout(coloraxis_showscale=False)
            st.plotly_chart(figure, width="stretch")
        with right:
            by_sector = results.groupby("sector", as_index=False)["pnl"].sum().sort_values("pnl")
            figure = px.bar(
                by_sector,
                x="pnl",
                y="sector",
                orientation="h",
                title="Stressed P&L by sector",
                color_discrete_sequence=["#c63d4f"],
            )
            st.plotly_chart(figure, width="stretch")

        waterfall = go.Figure(
            go.Waterfall(
                x=["Baseline", "Scenario loss", "Stressed value"],
                y=[run["pre_stress_value"], run["pnl"], run["post_stress_value"]],
                measure=["absolute", "relative", "total"],
                connector={"line": {"color": "#8ea0b5"}},
                decreasing={"marker": {"color": "#c63d4f"}},
                totals={"marker": {"color": "#16a6a1"}},
            )
        )
        waterfall.update_layout(title="Portfolio value bridge", showlegend=False)
        st.plotly_chart(waterfall, width="stretch")
        st.caption("Assumptions: " + " ".join(run["assumptions"]))

with portfolio_tab:
    st.subheader("Synthetic wholesale portfolio")
    columns = st.columns(3)
    columns[0].metric("Positions", portfolio["position_count"])
    columns[1].metric("Market value", money(portfolio["market_value"]))
    columns[2].metric("Classification", portfolio["data_classification"].title())
    left, right = st.columns(2)
    asset_frame = pd.DataFrame(
        [
            {"asset_type": key, "market_value": value}
            for key, value in portfolio["by_asset_type"].items()
        ]
    )
    sector_frame = pd.DataFrame(
        [{"sector": key, "market_value": value} for key, value in portfolio["by_sector"].items()]
    )
    with left:
        figure = px.pie(
            asset_frame,
            names="asset_type",
            values="market_value",
            hole=0.56,
            title="Market value by asset class",
            color_discrete_sequence=["#16a6a1", "#4e79a7", "#f4b942"],
        )
        st.plotly_chart(figure, width="stretch")
    with right:
        figure = px.bar(
            sector_frame.sort_values("market_value"),
            x="market_value",
            y="sector",
            orientation="h",
            title="Market value by sector",
            color_discrete_sequence=["#4e79a7"],
        )
        st.plotly_chart(figure, width="stretch")
    st.info("Every issuer, identifier, position, and sensitivity in this portfolio is fictional.")

with quality_tab:
    st.subheader("Validation and controls")
    st.caption(
        "Reproducible evidence for model behavior, data integrity, safe gating, and runtime health."
    )
    columns = st.columns(4)
    columns[0].metric("Sentiment backend", metrics["active_sentiment_backend"])
    columns[1].metric("Event backend", metrics["active_event_backend"])
    columns[2].metric("Dead letters", metrics["dead_letters"])
    columns[3].metric("Readiness", "Ready" if health["status"] == "ready" else "Check")
    metrics_path = ROOT / "docs/results/model_metrics.json"
    if metrics_path.exists():
        evaluation = json.loads(metrics_path.read_text(encoding="utf-8"))
        st.warning(evaluation["evaluation_notice"])
        sentiment_col, event_col, impact_mae_col, impact_corr_col = st.columns(4)
        sentiment_col.metric("Sentiment macro-F1", f"{evaluation['sentiment']['macro_f1']:.1%}")
        event_col.metric("Event macro-F1", f"{evaluation['event']['macro_f1']:.1%}")
        impact_mae_col.metric("Impact MAE", f"{evaluation['impact']['mae']:.2f} / 10")
        impact_corr_col.metric(
            "Impact Pearson r", f"{evaluation['impact']['pearson_correlation']:.2f}"
        )
        with st.expander("Evaluation protocol and per-class evidence"):
            st.json(evaluation)
    else:
        st.info("Run `make evaluate` to generate the reproducible evaluation report.")
    with st.expander("Scope and limitations", expanded=True):
        st.markdown(
            """
            - Scores use compact synthetic evaluation data and are not production accuracy claims.
            - Social text can contain sarcasm, rumors, and source bias.
              Low-confidence signals are gated.
            - Impact estimates severity and urgency, not a price target or forecast return.
            - Stress valuation is a transparent approximation, not regulatory capital analysis.
            - Live ingestion is optional; replay mode is the reproducible source of demo evidence.
            """
        )
