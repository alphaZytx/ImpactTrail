# Financial and Technical Assumptions

## Signal semantics

- Sentiment measures entity-specific financial tone.
- Impact measures severity and urgency on a 1–10 scale.
- Confidence is separate from sentiment magnitude and impact severity.
- A signal can be useful for monitoring without being automatically actionable.
- Event clusters use entity, event label, and UTC date for deterministic demo idempotency.

## Trigger semantics

- Event confidence must be at least 0.65.
- Impact confidence must be at least 0.60.
- Impact must be strictly greater than 7.0.
- A versioned scenario must exist for the primary event type.
- One event cluster can create only one run for a scenario/portfolio version.

## Portfolio and valuation

- All values are fictional USD-equivalent amounts.
- Loan loss is the increase in `EAD × PD × LGD` under the scenario.
- Bond loss is a duration/convexity approximation using rate and spread shifts.
- Equity derivatives use first-order monetary delta.
- Rate derivatives use signed DV01.
- FX derivatives use first-order monetary FX delta.
- Company-specific exposure match is 1.0; same sector 0.6; same country 0.4; residual 0.15.
- Market-wide signals apply a 1.0 match.
- Effective shocks are base shock × impact/10 × exposure match.

## Operational

- “Near real time” means the internal pipeline processes a fetched record immediately; provider
  publication/indexing latency is outside the application SLA.
- Replay is the release evidence path. Live ingestion is optional.
- UTC is used internally.
- SQLite is sufficient for hackathon-scale workload and is hidden behind a repository abstraction.

## Non-claims

The project does not claim price prediction, investment alpha, regulatory compliance, or production
accuracy. Scenarios and formulas are intentionally transparent and illustrative.

