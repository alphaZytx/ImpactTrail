# RiskPulse Data Card

## Summary

The submission uses only synthetic and fictional committed data. This makes the demonstration fully
redistributable, deterministic, and free of client/customer confidentiality concerns.

## Data assets

| Asset | Records | Purpose | Classification |
|---|---:|---|---|
| Mixed-source replay | 9 | End-to-end news/social ingestion | Synthetic |
| Company registry | 10 | Entity/ticker/alias resolution | Fictional |
| Wholesale portfolio | 72 | Stress testing | Synthetic |
| Sentiment gold set | 15 | Contract/baseline evaluation | Synthetic |
| Event gold set | 20 | Classification evaluation | Synthetic |

The SHA-256 manifest is `data/manifests/data_manifest.csv`. Portfolio generation is fixed at seed
`20261008`.

## Collection and generation

- Replay records were written in the shapes produced by the GDELT and Bluesky adapters.
- URLs use example or demonstration domains.
- Companies, tickers, counterparties, financial positions, engagement counts, labels, and values are
  fictional.
- The generator creates 32 loans, 24 bonds, and 16 derivatives.

## Sensitive information

There is no real personal, customer, client, or confidential S&P Global/Crisil data. Live provider
data is optional, local-only by default, and excluded from Git.

## Bias and limitations

- English-only evaluation.
- Small, intentionally balanced evaluation sets.
- Synthetic phrasing is simpler than live reporting or social language.
- Ratings and sensitivities exist to test calculations, not to describe real credit quality.
- Model performance on these files must not be generalized to real markets.

## Validation

`python scripts/validate_data.py` validates source diversity, schemas, record counts, asset-class
coverage, and manifest hashes. `make seed` regenerates and validates the portfolio.

