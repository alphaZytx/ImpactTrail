# ImpactTrail As-Built Design and Requirements Traceability

This document describes the code that is actually shipped. The root
`project_implementation_plan.md` is retained as the original planning artifact; it is not a claim
that every stretch goal was implemented.

## System boundary

ImpactTrail is a Python modular monolith built for an auditable, offline-safe jury demonstration:

1. GDELT news, Bluesky social posts, or the committed replay adapter produce one `RawDocument`
   contract.
2. Text is normalized and exact duplicate content is rejected.
3. Entity linking, financial sentiment, event classification, and explainable impact scoring create
   versioned `RiskSignal` objects.
4. Signals are persisted in SQLite and exposed through FastAPI.
5. A confidence-qualified signal triggers Module B only when its impact is strictly above `7.0` and
   its event has a direction-compatible configured scenario.
6. The stress engine values synthetic loans, bonds, and derivatives and reconciles position results
   to portfolio totals.
7. Streamlit presents evidence, decision gates, portfolio loss drivers, assumptions, and validation
   controls.

The default release path is deterministic and network-independent after dependency installation.
Live adapters are optional and use the same processing path.

## Decision semantics

- **Qualified signal:** the event is not `other`, an issuer is resolved or the event is genuinely
  systemic, event confidence is at least `0.65`, and impact confidence is at least `0.60`.
- **Stress trigger:** the signal is qualified, impact is strictly greater than `7.0`, and a versioned,
  direction-compatible scenario exists for the event class. A standalone rate-cut narrative cannot
  select the configured adverse rate-rise shock.
- **Monitor:** useful evidence that does not pass every qualification/trigger gate remains visible.
- **Unresolved issuer:** an issuer-specific narrative outside the reference universe is retained as
  unresolved and cannot trigger a full-portfolio stress.
- **Market-wide:** used only for systemic geopolitical, macroeconomic, or climate/natural-hazard
  narratives without a specific resolved issuer.

Impact measures estimated severity and urgency. It is not a price forecast. A triggered scenario is
a standardized adverse stress, not a prediction that its shocks will occur.

## Implemented components

| Capability | Implementation | Evidence |
|---|---|---|
| Two unstructured sources | GDELT and Bluesky HTTP adapters plus shape-equivalent replay | `src/impacttrail/ingestion/`, adapter integration tests |
| Entity resolution | Fictional issuer/ticker/alias registry, systemic and unresolved states | `processing/entity_linker.py`, entity and E2E tests |
| Sentiment | Bounded finance lexicon by default; pinned optional FinBERT backend | `nlp/sentiment.py`, synthetic-set evaluation |
| Event classification | Versioned ten-class taxonomy with honest `other` outcome | `nlp/event_classifier.py`, macro-F1 evaluation |
| Impact | Seven-factor, weighted 1–10 severity model | `nlp/impact.py`, synthetic-set MAE/correlation evaluation |
| Machine-readable output | Pydantic schema, filtered API, OpenAPI, per-signal JSON download | `domain/signals.py`, `api/app.py`, API tests |
| Module B | Five scenario families and asset-specific valuation for loans, bonds, derivatives | `stress_testing/`, reconciliation and boundary tests |
| Analyst experience | Priority view, decision trace, signal explorer, stress lab, portfolio and controls | `dashboard/app.py` |
| Reproducibility | Fixed replay, fixed-seed portfolio, SHA-256 data manifest, CI and release gate | `data/`, `scripts/`, `.github/workflows/ci.yml` |

## Requirement traceability

| Requirement | Status | Reproducible proof |
|---|---|---|
| Ingest at least two source types | Complete | Replay contains GDELT-shaped news and Bluesky-shaped social records; live adapters share the interface |
| Emit sentiment `[-1, 1]` | Complete | `SentimentResult` validation and NLP tests |
| Emit required event categories | Complete | Versioned taxonomy includes all five required examples plus five risk-relevant classes |
| Emit impact `[1, 10]` | Complete | `ImpactResult` validation, component breakdown, and evaluation report |
| Provide downstream-consumable output | Complete | `/api/v1/signals`, OpenAPI, and downloadable JSON |
| Use event and impact in Module B | Complete | Automatic strict-threshold scenario trigger in the end-to-end test |
| Include loans, bonds, derivatives | Complete | Fixed 72-position portfolio and asset-class valuation tests |
| Show before/after portfolio value | Complete | Stress API and dashboard metrics, charts, position reconciliation |
| Source, deck, data, license, instructions | Complete except owner-supplied links/identity | Strict `make submission` gate reports the remaining fields |

## Deliberate boundaries

- The committed evaluation data is small, synthetic, English-only, and intended for deterministic
  contract evidence—not production accuracy estimation.
- Event clustering in the demo uses resolved entity, event class, a six-hour window, and matched-term
  overlap. It demonstrates bounded corroboration and idempotency, but is not semantic production
  clustering.
- Exact normalized content hashes are deduplicated inside a 24-hour window; provider record IDs stay
  idempotent for the life of the demo store so recurring later headlines are not silently discarded.
- SQLite is the implemented signal store. JSON is exported per signal through the dashboard/API;
  there is no batch JSONL/CSV signal exporter in v1.
- Live-source availability, provider indexing latency, and model downloads are outside the offline
  demo guarantee.
- Valuations are transparent approximations and are not regulatory capital, CCAR, ICAAP, VaR, or
  investment advice.

## Release evidence

Run:

```bash
make release
```

This checks formatting, lint, strict typing, dataset integrity, automated tests, branch-aware
coverage, model evaluation, required files, and the seven-page deck. Before final submission, run:

```bash
make submission
```

The strict gate also rejects placeholder candidate details, a missing public GitHub clone URL, a
missing YouTube demo URL, repository naming violations, and placeholder text in the deck. Public
access and unlisted-video playback must still be checked manually in a private browser window.
