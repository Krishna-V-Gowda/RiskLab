# Methodology

## Research question

Which common long-only allocation rules remain comparatively stable out of sample when estimation windows are finite, distributions are heavy-tailed, regimes change, and rebalancing incurs explicit costs?

## Controlled process

RiskLab uses one deterministic synthetic path with four predeclared regimes: calm, correlation shock, recovery, and inflation volatility. Three heavy-tailed latent factors and idiosyncratic Student-t innovations generate eight assets. This creates a known stress environment without pretending that the process is a calibrated representation of a particular exchange or security universe.

## Temporal protocol

At decision day `t`, estimators receive exactly `returns[t-window:t]`. The position is applied to return `t`. Future observations are inaccessible to the allocator. A metamorphic test changes all observations after a cutoff and requires all earlier target weights to remain bit-identical.

## Covariance estimation

The sample minimum-variance method uses an unbiased empirical covariance followed by positive-semidefinite repair. The shrinkage path implements Oracle Approximating Shrinkage with target `mu I` and its finite-sample coefficient. The report retains shrinkage intensity and condition numbers.

## Allocation objectives

- Equal weight: `w_i = 1/N`.
- Inverse volatility: `w_i ∝ 1/sqrt(Σ_ii)`.
- Minimum variance: minimize `wᵀΣw`.
- Risk parity: minimize squared deviations of component variance contributions from their equal target.
- Minimum CVaR: minimize `ζ + 1/((1-α)T) Σu_t` subject to `u_t ≥ -r_tᵀw - ζ`.

All optimized portfolios satisfy `Σw=1`, `w≥0`, and a configured concentration cap when feasible.

## Execution and costs

Portfolio weights drift after each daily return. On rebalance days, one-way turnover is `0.5 Σ|w_target - w_pretrade|`; cost is turnover times the configured basis-point rate. Initial formation cost is excluded and declared in every report.

## Uncertainty

The paired circular moving-block bootstrap resamples the daily return difference between each candidate and equal weight. The retained interval is for annualized arithmetic mean-return difference conditional on the generated path and block length. It is not a confidence interval over real-world markets.

## Prespecified sensitivity scenarios

1. Base: long window, monthly rebalance, 10 bps.
2. Short window: less estimation history.
3. High cost: 25 bps.
4. Low frequency: quarterly-like rebalance.

No scenario is selected after observing its outcome.
