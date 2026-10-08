# RiskPulse - S&P Global & Crisil Campus Hackathon 2026

**Candidate Name:** `[REPLACE WITH FULL NAME]`  
**College Email ID:** `[REPLACE WITH COLLEGE EMAIL]`  
**College / Campus:** `[REPLACE WITH COLLEGE NAME]`  
**Demo Video Link:** `[ADD UNLISTED YOUTUBE LINK]`  
**Slide Deck:** [docs/presentation.pdf](docs/presentation.pdf)

> Educational prototype. RiskPulse is not investment advice and is not a regulatory stress-testing system.

## 1. Project Overview / Problem Statement & Approach

Financial risk teams face more unstructured information than they can review consistently. News and
social posts arrive with different formats, repeated coverage, ambiguous entities, and no direct link
to portfolio exposure. RiskPulse turns that narrative stream into an auditable contract: entity-level
sentiment from `-1` to `1`, an explicit financial-event category, and an explainable severity score
from `1` to `10`.

The platform processes GDELT-shaped news and Bluesky-shaped social text through one pipeline. A
deterministic offline replay makes the result reproducible; optional live adapters use the same code
path. Signals carry confidence, evidence, provenance, reason codes, model versions, and idempotency
keys. When a supported event is actionable and its impact is strictly greater than `7`, RiskPulse
automatically runs a transparent scenario against a synthetic portfolio of loans, bonds, and
derivatives. The dashboard connects the original narrative to portfolio value-at-risk drivers without
manual data transfer.

## 2. Architecture & Tech Stack

![RiskPulse architecture](docs/architecture.png)

The implementation is a modular Python monolith: source adapters → normalization/deduplication →
entity linking → sentiment/event/impact analysis → SQLite signal store/API → automatic stress engine
→ Streamlit dashboard. This structure is simple to run for judges while retaining testable module
boundaries.

- Python 3.11, FastAPI, Pydantic, SQLAlchemy, SQLite
- HTTPX adapters for GDELT and Bluesky; deterministic JSONL replay
- Finance lexicon offline model and optional `ProsusAI/finbert` backend
- Versioned rule-based event taxonomy with explicit abstention
- Explainable seven-factor impact score and confidence gates
- Streamlit, Plotly, and pandas dashboard
- pytest, coverage, Ruff, mypy, GitHub Actions, Docker Compose

Detailed design: [project_implementation_plan.md](project_implementation_plan.md)  
Model card: [docs/model_card.md](docs/model_card.md)  
Assumptions: [docs/assumptions.md](docs/assumptions.md)

## 3. Dataset Used

Every committed runtime dataset is synthetic, compact, redistributable, and documented in
[data/README.md](data/README.md). No confidential or real client data is used.

- 9 mixed-source replay records, including an exact duplicate to verify idempotency
- 10 fictional companies with aliases and cashtags
- 72 fictional wholesale positions: 32 loans, 24 bonds, and 16 derivatives
- 15 finance-sentiment and 20 financial-event evaluation examples
- SHA-256 provenance manifest at `data/manifests/data_manifest.csv`

Live source content is optional and is written only to Git-ignored runtime storage. Synthetic records
are clearly labeled and never represented as real GDELT/Bluesky content.

## 4. Quickstart & Installation

Runtime: **Python 3.11**. Tested on macOS; CI tests Linux on GitHub Actions.

```bash
git clone <your-public-repository-url>
cd <college>-<candidate-name>-hackathon
make setup
make seed
make doctor
make demo
```

Start the API:

```bash
make api
```

In another terminal, start the dashboard:

```bash
make dashboard
```

Open:

- Dashboard: <http://127.0.0.1:8501>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Readiness: <http://127.0.0.1:8000/readyz>

### Direct commands without Make

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/generate_portfolio.py
.venv/bin/python scripts/update_data_manifest.py
.venv/bin/python scripts/validate_data.py
.venv/bin/python -m riskpulse.cli replay --fixture data/demo/mixed_source_events.jsonl
.venv/bin/uvicorn riskpulse.api.app:create_app --factory --port 8000
```

### Docker Compose

```bash
docker compose up --build
```

### Optional FinBERT backend

The default `auto` mode uses FinBERT when its optional dependencies and weights are prepared; it
otherwise selects the tested offline finance lexicon.

```bash
make models
RISKPULSE_MODEL_BACKEND=finbert make demo
```

Model downloads are disabled by default during application startup. The five-minute demo never
downloads weights.

### Optional live ingestion

```bash
.venv/bin/python -m riskpulse.cli live --query 'financial markets'
# Or continuously poll both providers every five minutes:
make live
```

Live adapters use bounded exponential backoff for rate limits and transient provider errors. Live
operation still requires network availability and provider compliance; replay remains the official
reproducible evidence path.

## 5. Key Results & Domain Impact

The committed replay currently produces:

- 9 fetched inputs, 8 unique documents, and 1 exact duplicate rejected
- 9 entity/event risk signals from news and social source shapes
- 4 distinct automatic stress runs with no duplicate trigger
- 72 reconciled position-level valuations across loans, bonds, and derivatives
- Zero replay failures

On the compact synthetic gold sets, the transparent offline baselines produce:

| Model | Samples | Macro-F1 | Accuracy |
|---|---:|---:|---:|
| Finance sentiment lexicon | 15 | 100.00% | 100.00% |
| Event taxonomy rules | 20 | 94.67% | 95.00% |

These results prove deterministic behavior on the submitted examples; they are **not production
accuracy claims**. Exact reproducible metrics are in
[docs/results/model_metrics.json](docs/results/model_metrics.json).

RiskPulse demonstrates the domain workflow that matters: a risk analyst can move from an external
narrative to a confidence-gated, explainable signal and then to asset/sector/country portfolio loss
drivers without manual copying. The system also shows its uncertainty and refuses automatic action
when confidence or scenario applicability is insufficient.

## 6. Test and Quality Commands

```bash
make test       # 32 automated test cases
make coverage   # branch-aware coverage; release floor 85%
make quality    # formatting, linting, type checks, data validation
make evaluate   # reproducible synthetic-set model metrics
make release    # complete local release gate
```

The test suite covers source mapping, malformed/duplicate handling, entity matching, NLP ranges,
impact components, API contracts, retry behavior, cross-source corroboration, strict trigger
boundaries, idempotency, all three asset classes, and portfolio reconciliation.

## 7. API Examples

Analyze a new text:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H 'Content-Type: application/json' \
  -d '{"text":"Nova Bank downgraded after default and missed payment"}'
```

Query high-impact signals:

```bash
curl 'http://127.0.0.1:8000/api/v1/signals?min_impact=7&actionable=true'
```

## 8. Limitations and Responsible Use

- The submitted data and evaluation sets are intentionally compact and synthetic.
- Sentiment is entity-specific financial tone, not a forecast return.
- Impact is modeled severity/urgency, not a predicted percentage price move.
- Source quality priors and scenarios contain documented modeling judgment.
- Social text can contain rumors, sarcasm, and manipulation.
- Stress formulas are transparent approximations, not regulatory capital models.
- The repository must be personalized with candidate identity and the final public video/repository
  links before submission.

## 9. License and Acknowledgements

Source code and committed synthetic project data are released under the [MIT License](LICENSE).
External services and optional model weights retain their own terms. Material AI assistance should be
acknowledged honestly in the final submission, consistent with the hackathon guidelines.
