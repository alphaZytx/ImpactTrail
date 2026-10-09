# ImpactTrail Jury Q&A Brief

Use these as concise answers, not a memorized script. Lead with the design decision, then the evidence
or limitation.

## Why is this more useful than sentiment analysis?

Sentiment alone does not say what happened, how severe it may be, whether the result is trustworthy,
or where the bank is exposed. ImpactTrail joins source evidence, entity, event, severity, policy gates,
scenario, and position-level loss drivers in one traceable contract.

## Where is the AI/NLP?

The release engine separates four bounded components: entity resolution, financial sentiment, event
classification, and impact scoring. The offline default is intentionally deterministic and
explainable; optional FinBERT is pinned but never downloaded during a jury demo. The current compact
synthetic evaluation proves reproducibility, not generalization. A production decision would compare
the baseline against time-split public data before promotion.

## Why use rules instead of an LLM?

For a five-minute risk-control prototype, deterministic rules make the output reproducible,
inspectable, cheap, and safe offline. The architecture keeps model boundaries replaceable. A more
complex model earns promotion only if it improves held-out performance and preserves calibration,
latency, and traceability.

## What exactly does impact mean?

Impact is estimated severity and urgency on a 1–10 scale—not expected return. It combines event
severity, entity relevance, tone intensity, model confidence, cross-source corroboration, novelty,
and source quality. The dashboard reconstructs the weighted score. On 20 synthetic rubric examples,
the baseline has MAE 1.15 and Pearson correlation 0.8521; those are contract-evidence numbers, not
market-validation claims.

## Why does a signal trigger stress testing?

It must pass four independent gates: event confidence at least 0.65, impact confidence at least 0.60,
impact strictly above 7.0, and a configured scenario. An unresolved issuer, `other` classification,
low confidence, low severity, or unsupported event remains visible but cannot auto-trigger.

## Could an unknown company shock the whole portfolio?

No. Issuer-specific text that does not match the bounded fictional universe is marked unresolved with
zero entity confidence and is ineligible for action. Only genuinely systemic macroeconomic,
geopolitical, or climate events can use the market-wide state.

## Is the scenario a forecast of what will happen?

No. Detection is a trigger to run a standardized adverse scenario. The scenario is a vulnerability
assessment, not a prediction of shock direction or probability. The UI and documentation keep impact,
confidence, and valuation assumptions separate.

## How do you prevent duplicate actions?

Exact normalized content is deduplicated. Related fixture records share an event cluster, and the
database enforces one stress run per cluster, scenario version, and portfolio version. The Nova news
and social records therefore enrich one cluster without creating a second credit stress.

## How is the portfolio valued?

- Loans: change in expected loss using EAD × PD × LGD.
- Bonds: duration/convexity approximation with rate and credit-spread shocks.
- Equity, rate, and FX derivatives: first-order delta or DV01 sensitivity.

Every position result rolls up to pre-value + P&L = post-value; the hero credit run reconciles to
`$0.00`.

## Why SQLite and a modular monolith?

The evaluated workload is small and the demo must start reliably. SQLite removes infrastructure risk,
while repository and service boundaries preserve a clean path to PostgreSQL, a queue, and separately
scaled workers when measured throughput requires them.

## How is “real-time” supported?

Fetched records are processed immediately in the internal pipeline, and live adapters support bounded
retries and polling. Provider publishing/indexing latency is outside the application boundary. Replay
is the formal evidence path so network availability cannot invalidate the demo.

## What are the most important limitations?

English-only synthetic evaluation, simple rules/lexicons, day-level demo clustering, expert-defined
impact/scenario assumptions, and first-order valuation. The next validation step is a larger
independently reviewed, time-split public dataset with source slices, calibration, drift monitoring,
and analyst feedback.

## What business outcome does this enable?

It gives an analyst one prioritized, auditable path from external narrative to affected exposure and
loss driver. That reduces manual handoffs, makes thresholds consistent, preserves human review, and
creates evidence that can be challenged rather than hiding judgment in an opaque score.
