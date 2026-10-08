# Five-Minute Demo Script

## Preflight

```bash
make doctor
make demo
make api
# Separate terminal
make dashboard
```

Open the dashboard at `http://127.0.0.1:8501` and API docs at
`http://127.0.0.1:8000/docs`. Disable notifications and close unrelated windows.

## Script

### 0:00–0:25 — Problem

“Risk teams receive news and social signals faster than they can normalize, assess, and connect to
portfolio exposure. RiskPulse converts each narrative into an auditable risk signal and an automatic,
explainable portfolio stress result.”

### 0:25–0:50 — Architecture

Show the architecture slide: GDELT-shaped news and Bluesky-shaped social input use one pipeline;
replay makes it reliable; API/dashboard consume the same stored signal contract.

### 0:50–1:35 — Replay

Press **Run deterministic replay**. Point out 9 fetched records, 8 unique documents, one duplicate,
news + social sources, and zero failures.

### 1:35–2:30 — Signal

Open Nova Bank. Show:

- Negative entity-level sentiment.
- Credit-event classification.
- Impact above 7 with independent confidence.
- Evidence excerpt, reason codes, source, timestamps, and model version.
- Duplicate/idempotency behavior.

### 2:30–3:45 — Stress test

Open the automatically created credit scenario. Show exact shock assumptions, pre/post portfolio
value, loss percentage, asset-class loss, sector drivers, and value bridge. Explain loan expected-loss,
bond duration/spread, and derivative sensitivity methods.

### 3:45–4:20 — Quality

Show the Model & Data Quality tab. State clearly that metrics use compact synthetic sets; highlight
automated tests, at least 85% branch-aware package coverage, deterministic data hashes, and
abstention/confidence gates.

### 4:20–4:50 — Impact and limitations

“The value is not just a sentiment label. It is the traceable path from narrative to affected entity,
severity, scenario, and portfolio driver. This remains an educational prototype: impact is not a
return forecast and the stress result is not regulatory capital analysis.”

### 4:50–5:00 — Buffer

Stop rather than adding an unplanned feature tour.

## Recovery

- API unavailable: show `make doctor`, then restart `make api`.
- Empty dashboard: run `make demo` and refresh.
- Network unavailable: replay needs no provider access.
- UI issue: use `http://127.0.0.1:8000/docs` to demonstrate the same workflow.
