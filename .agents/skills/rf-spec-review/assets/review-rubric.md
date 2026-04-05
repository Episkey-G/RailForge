# Review Rubric

## Deterministic First

- Deterministic gate failures are blocking.
- Runtime or outcome failures are blocking.

## Compliance Review

- Backend and frontend review findings must be merged without dropping critical issues.
- A model review cannot override a deterministic failure.

## Verdict

- `approved`: deterministic gates pass and no blocking review findings remain.
- `failed`: any blocking deterministic or review issue remains.
