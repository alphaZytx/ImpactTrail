# ImpactTrail Data Card

All committed runtime data is compact, synthetic, and safe to redistribute. No confidential,
client, customer, or proprietary S&P Global/Crisil information is used.

## Contents

- `demo/mixed_source_events.jsonl`: synthetic records shaped like GDELT news and Bluesky posts.
  They are used by deterministic replay and are not represented as content collected from those
  services.
- `evaluation/sentiment_gold.csv`: 90-example balanced finance-language sentiment challenge set
  with positive, neutral, and negative slices.
- `evaluation/events_gold.csv`: 100-example balanced event/impact challenge set covering all ten
  taxonomy labels and varied single-cue, multi-cue, severity, direction, and competing-cue cases.
- `reference/companies.csv`: fictional issuer/ticker registry for deterministic entity linking.
- `synthetic/wholesale_portfolio.csv`: fixed-seed fictional loans, bonds, and derivatives.
- `manifests/data_manifest.csv`: file-level provenance and SHA-256 hashes.

## Assumptions

- Currency figures are USD-equivalent demo units.
- Ratings, PD, LGD, duration, delta, and DV01 values are illustrative.
- Event impact labels express a review rubric, not observed future price returns.
- Impact evaluation standardizes source shape, entity relevance, corroboration, and novelty so the
  deterministic score comparison is reproducible; the exact protocol is emitted with the metrics.
- Social engagement values are synthetic and are not used as personal data.
- Live provider payloads, if enabled, are written only to ignored runtime storage.

## Reproduction

Run `make seed` to regenerate the evaluation sets and portfolio with fixed inputs and validate every
file.
Run `make evaluate` to reproduce model metrics.
