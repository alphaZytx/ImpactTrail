# Five-Minute Demo Script

## Preflight

```bash
make doctor
make api
# Separate terminal
make dashboard
```

Open the dashboard at `http://127.0.0.1:8501` and API docs at
`http://127.0.0.1:8000/docs`. Disable notifications and close unrelated windows.

## Script

### 0:00–0:25 — Problem

“Risk teams receive news and social signals faster than they can normalize, assess, and connect to
portfolio exposure. ImpactTrail converts each narrative into an auditable risk signal and an automatic,
explainable portfolio stress result.”

### 0:25–0:50 — Architecture

Show the architecture slide: GDELT-shaped news and Bluesky-shaped social input use one pipeline;
replay makes it reliable; API/dashboard consume the same stored signal contract.

### 0:50–1:20 — Replay proof

Press **Reset & run demo replay**. The action clears only local runtime records and rebuilds the same
fixture every time. Point to all six counters: 9 fetched, 8 processed, 1 duplicate, 9 signals, 4
stress runs, and 0 failures.

### 1:20–2:35 — One auditable decision trace

Open **Decision trace**; Nova Bank is already selected because signals are prioritized by impact.
Follow the numbered chain:

- Two records from independent news and social source types form one event cluster.
- The structured signal resolves Nova Bank, classifies a credit event, shows negative financial tone,
  and explains an impact score above 7.
- Event confidence, impact confidence, strict severity, and scenario-compatibility gates all pass.
- The factor chart reconstructs the impact score from the visible weighted components.

Say: “A label does not cause action by itself; all four policy gates must pass.”

### 2:35–3:40 — Portfolio consequence

Stay in the trace for the linked credit scenario: `-$7.39M`, `-1.80%`, the top sector driver, and
`$0.00` reconciliation error. Then open **Stress lab** to show formatted shock assumptions,
pre/post value, asset-class and sector loss, and the value bridge. Briefly explain loan expected loss,
bond duration/spread, and derivative delta/DV01 methods.

### 3:40–4:20 — Safety and validation

Open **Signal explorer** and point to Orion Pharma's honest `other` result. Explain that an unknown
issuer remains unresolved and cannot become a market-wide stress. Open **Validation & controls** and
state the limitation before the metrics: compact synthetic sets verify deterministic contracts, not
production accuracy. Show event/sentiment evidence, impact MAE/correlation, hashes, and readiness.

### 4:20–4:50 — Impact and limitations

“The value is not just a sentiment label. It is the traceable path from narrative to affected entity,
severity, policy decision, and portfolio driver—with the evidence and assumptions attached. This is
an educational prototype: impact is not a return forecast and the stress result is not regulatory
capital analysis.”

### 4:50–5:00 — Buffer

Stop rather than adding an unplanned feature tour.

## Recovery

- API unavailable: show `make doctor`, then restart `make api`.
- Empty dashboard: press **Reset & run demo replay** or run `make demo`, then refresh.
- Network unavailable: replay needs no provider access.
- UI issue: use `http://127.0.0.1:8000/docs` to demonstrate the same workflow.
