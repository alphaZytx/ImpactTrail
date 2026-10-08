# ADR 001: Modular Monolith with Deterministic Replay

## Status

Accepted for hackathon release 1.0.

## Context

The application needs source adapters, NLP, storage, an API, stress testing, and a dashboard, but the
submission must be easy for a judge to run and demonstrate within five minutes. Live data providers
can fail independently.

## Decision

Use one typed Python package with explicit module boundaries and SQLite. Expose services through a
versioned FastAPI contract. Keep the Streamlit dashboard as an API consumer. Make fixture replay a
first-class source adapter, not a separate mock pipeline.

## Consequences

- Setup and diagnosis remain simple.
- Unit/integration tests can isolate every boundary.
- Offline demonstration exercises real normalization, inference, persistence, triggering, and
  valuation.
- SQLite limits horizontal scale, which is acceptable for the submission.
- Components can be extracted later because adapters/repositories/domain contracts are separated.

