# RiskPulse Model Card

## Model overview

RiskPulse v1.0 combines four bounded components rather than presenting one opaque model:

1. Entity resolution from a versioned fictional issuer/alias registry.
2. Finance sentiment from an offline lexicon or optional ProsusAI FinBERT.
3. Event classification from a versioned taxonomy/rule baseline.
4. Explainable impact scoring from seven normalized factors.

## Intended use

- Educational analysis of financial news/social text.
- Demonstrating a machine-readable risk-signal contract.
- Triggering transparent illustrative scenarios on a synthetic portfolio.
- Comparing deterministic replay outputs and model backends.

## Out-of-scope use

- Investment advice or automated trading.
- Credit decisions about a real person or company.
- Regulatory, capital, CCAR, ICAAP, or production market-risk reporting.
- A factuality or misinformation classifier.

## Outputs

- Sentiment score `[-1, 1]`, label, confidence, probabilities, and backend.
- Primary event label, optional secondary labels, matched terms, and confidence.
- Impact score `[1, 10]`, confidence, horizon, and component breakdown.
- Entity, evidence excerpt, provenance, model version, warnings, and actionability.

## Evaluation

`python scripts/evaluate_models.py` evaluates the offline baselines on committed synthetic gold sets.
The current result is 100.00% sentiment macro-F1 on 15 samples and 94.67% event macro-F1 on 20
samples. The sets were designed for contract verification and are too small/synthetic to estimate
real-world accuracy. Results are never presented without that limitation.

## Impact score

Impact estimates severity and urgency. It combines event severity (30%), entity relevance (15%),
sentiment intensity (10%), model confidence (10%), corroboration (15%), novelty (10%), and source
quality (10%). It does not predict return direction or magnitude.

## Confidence and abstention

Automatic action requires event confidence of at least 0.65, impact confidence of at least 0.60, a
supported event scenario, and impact strictly greater than 7.0. `other` and unresolved/low-confidence
signals remain inspectable but are not forced into automatic action.

## Known limitations

- Rules can miss paraphrases and novel event language.
- Lexicon sentiment is weak on negation, mixed tone, and sarcasm.
- FinBERT is optional and may still be poorly calibrated on social posts.
- Company aliases are limited to the configured universe.
- Source-quality priors and impact severity contain expert judgment.
- There is no claim of multilingual equivalence or market-return causality.

## Reproducibility

Configuration, code, data hashes, and backend names are stored with the project. The default demo is
offline after setup. Optional model dependencies are separate in `requirements-ml.txt`; application
startup never downloads weights unless explicitly enabled.

The optional FinBERT checkpoint is pinned to Hugging Face revision
`4556d13015211d73dccd3fdd39d39232506f3e43`.
