from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_API_URL = os.getenv("RISKPULSE_API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="RiskPulse | Financial Risk Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#10233f; --teal:#16a6a1; --gold:#f4b942; --paper:#f5f7fb; }
    .stApp { background: linear-gradient(180deg,#f8fafc 0%,#eef3f8 100%); }
    [data-testid="stSidebar"] { background:#10233f; color:white; }
    [data-testid="stSidebar"] * { color:white; }
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


with st.sidebar:
    st.markdown("## ◈ RiskPulse")
    st.caption("Financial risk intelligence")
    api_url = st.text_input("API URL", DEFAULT_API_URL)
    if st.button("Run deterministic replay", type="primary", use_container_width=True):
        try:
            result = api_post(
                api_url, "/api/v1/replays", {"fixture": "data/demo/mixed_source_events.jsonl"}
            )
            st.success(
                f"Replay complete: {result['signals']} signals, "
                f"{result['stress_runs']} new stress runs"
            )
        except Exception as exc:
            st.error(f"Replay failed: {exc}")
    if st.button("Refresh", use_container_width=True):
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
    st.error("RiskPulse API is not ready.")
    st.code("make demo\nmake api\n# In another terminal:\nmake dashboard", language="bash")
    st.caption(str(exc))
    st.stop()

tabs = st.tabs(["Overview", "Signal explorer", "Stress lab", "Portfolio", "Model & data quality"])

with tabs[0]:
    columns = st.columns(5)
    columns[0].metric("Documents", metrics["documents"])
    columns[1].metric("Signals", metrics["signals"])
    columns[2].metric("Actionable", metrics["actionable_signals"])
    columns[3].metric("Stress runs", metrics["stress_runs"])
    latest_loss = stress_runs[0]["pnl"] if stress_runs else 0
    columns[4].metric("Latest stressed P&L", money(latest_loss))

    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Latest risk signals")
        if not signals:
            st.info("Run the deterministic replay to populate the engine.")
        for signal in signals[:5]:
            impact = signal["impact"]["score"]
            status_label = "ACTIONABLE" if signal["actionable"] else "MONITOR"
            st.markdown(
                f"""<div class="signal-card"><b>{signal["entity"]["name"]}</b> · {status_label}<br>
                <span style="color:#50647f">{signal["event"]["label"].replace("_", " ").title()} ·
                impact {impact:.1f}/10 · sentiment {signal["sentiment"]["score"]:+.2f} ·
                {signal["source"]["name"]}</span></div>""",
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
            st.plotly_chart(figure, use_container_width=True)

    st.markdown(
        '<div class="notice"><b>Interpretation:</b> impact measures estimated '
        "severity and urgency, "
        "not a predicted return. Confidence gates control automatic portfolio actions.</div>",
        unsafe_allow_html=True,
    )

with tabs[1]:
    st.subheader("Auditable signal explorer")
    if signals:
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
                "actionable": item["actionable"],
            }
            for item in signals
        ]
        frame = pd.DataFrame(signal_rows)
        st.dataframe(
            frame.drop(columns=["signal_id"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "impact": st.column_config.ProgressColumn(min_value=1, max_value=10, format="%.1f"),
                "sentiment": st.column_config.NumberColumn(format="%+.2f"),
            },
        )
        selection = st.selectbox(
            "Inspect signal",
            options=range(len(signals)),
            format_func=lambda index: (
                f"{signals[index]['entity']['name']} · "
                f"{signals[index]['event']['label'].replace('_', ' ').title()} · "
                f"{signals[index]['impact']['score']:.1f}/10"
            ),
        )
        selected = signals[selection]
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
            file_name=f"riskpulse-signal-{selected['signal_id']}.json",
            mime="application/json",
        )

with tabs[2]:
    st.subheader("Strategic portfolio stress lab")
    if not stress_runs:
        st.info("No qualifying high-impact event has triggered a stress run yet.")
    else:
        selected_run_index = st.selectbox(
            "Stress run",
            options=range(len(stress_runs)),
            format_func=lambda index: (
                f"{stress_runs[index]['scenario_name']} · impact "
                f"{stress_runs[index]['trigger_impact']:.1f}/10"
            ),
        )
        run = stress_runs[selected_run_index]
        columns = st.columns(4)
        columns[0].metric("Pre-stress value", money(run["pre_stress_value"]))
        columns[1].metric("Post-stress value", money(run["post_stress_value"]))
        columns[2].metric("Stressed P&L", money(run["pnl"]), f"{run['pnl_percent']:.2%}")
        columns[3].metric("Impact trigger", f"{run['trigger_impact']:.1f}/10")
        st.markdown(f"**{run['scenario_name']}** — {run['scenario_description']}")
        shock_frame = pd.DataFrame(
            [
                {"risk_factor": key.replace("_", " ").title(), "value": value}
                for key, value in run["base_shocks"].items()
            ]
        )
        st.dataframe(shock_frame, use_container_width=True, hide_index=True)

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
            st.plotly_chart(figure, use_container_width=True)
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
            st.plotly_chart(figure, use_container_width=True)

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
        st.plotly_chart(waterfall, use_container_width=True)
        st.caption("Assumptions: " + " ".join(run["assumptions"]))

with tabs[3]:
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
        st.plotly_chart(figure, use_container_width=True)
    with right:
        figure = px.bar(
            sector_frame.sort_values("market_value"),
            x="market_value",
            y="sector",
            orientation="h",
            title="Market value by sector",
            color_discrete_sequence=["#4e79a7"],
        )
        st.plotly_chart(figure, use_container_width=True)
    st.info("Every issuer, identifier, position, and sensitivity in this portfolio is fictional.")

with tabs[4]:
    st.subheader("Model and data quality")
    columns = st.columns(4)
    columns[0].metric("Sentiment backend", metrics["active_sentiment_backend"])
    columns[1].metric("Event backend", metrics["active_event_backend"])
    columns[2].metric("Dead letters", metrics["dead_letters"])
    columns[3].metric("Readiness", "Ready" if health["status"] == "ready" else "Check")
    metrics_path = ROOT / "docs/results/model_metrics.json"
    if metrics_path.exists():
        evaluation = json.loads(metrics_path.read_text(encoding="utf-8"))
        st.warning(evaluation["evaluation_notice"])
        sentiment_col, event_col = st.columns(2)
        sentiment_col.metric("Sentiment macro-F1", f"{evaluation['sentiment']['macro_f1']:.1%}")
        event_col.metric("Event macro-F1", f"{evaluation['event']['macro_f1']:.1%}")
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
