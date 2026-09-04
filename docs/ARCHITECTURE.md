# Architecture

```text
fixed seed + regime specification
            |
            v
   heavy-tailed simulator -----> immutable return matrix + provenance hash
            |
            v
 strict trailing window [t-W,t)
            |
     +------+------------------------------+
     | covariance estimators               | empirical / OAS / PSD repair
     | allocation objectives               | EW / IV / MV / OAS-MV / RP / CVaR
     +------+------------------------------+
            |
            v
 pre-trade weights -> one-way turnover -> transaction cost
            |
            v
      day-t return -> weight drift -> next decision
            |
            v
 metrics + paired block bootstrap + failure counts
            |
            v
 JSON / CSV / Markdown / deterministic figures
```

## Boundary decisions

The package is intentionally a single-process scientific application. A service layer, database, message bus, and distributed scheduler would not improve the experiment’s validity. Arrays are immutable by convention at module boundaries. Randomness enters only through explicitly seeded `numpy.random.Generator` instances.

## Numerical paths

- Covariance matrices are symmetrized and eigenvalue-clipped before constrained solves.
- SLSQP handles smooth long-only minimum-variance and risk-parity objectives.
- HiGHS solves the Rockafellar–Uryasev linear representation of empirical CVaR.
- A failed optimizer retains the previous portfolio and increments a failure counter; it is not silently relabeled as success.
