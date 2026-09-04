# RiskLab experiment report

> Controlled synthetic evidence. These are not historical returns and not investment advice.

## Design

- Seed: `20260903`
- Simulated observations: `1800` days × `8` assets
- Heavy-tailed regimes: calm, correlation_shock, recovery, inflation_volatility
- Bootstrap resamples per method/scenario comparison: `500`
- Circular moving-block length: `21` observations
- Initial portfolio formation costs are excluded; subsequent one-way turnover is charged.

## Covariance diagnostic at the first base-scenario rebalance

| Diagnostic | Value |
|---|---:|
| empirical condition number | 8.23262 |
| oas condition number | 7.42653 |
| oas shrinkage | 0.0479183 |
| condition number ratio empirical to oas | 1.10854 |

## Scenario results

### base

Window `252`, rebalance every `21` days, cost `10.0` bps per unit of one-way turnover.

| Method | Ann. return | Ann. vol | Sharpe | Max DD | Turnover | Failures | 95% annualized mean-return diff vs EW |
|---|---:|---:|---:|---:|---:|---:|---:|
| equal weight | -15.14% | 16.12% | -0.937 | -68.55% | 1.25 | 0 | baseline |
| inverse volatility | -13.70% | 15.06% | -0.902 | -64.95% | 1.44 | 0 | [0.12%, 2.79%] |
| sample min variance | -9.74% | 12.61% | -0.749 | -57.45% | 3.39 | 0 | [0.11%, 11.10%] |
| oas min variance | -9.65% | 12.62% | -0.740 | -57.39% | 3.44 | 0 | [0.48%, 10.93%] |
| risk parity | -13.17% | 14.53% | -0.898 | -63.53% | 1.64 | 0 | [0.05%, 4.22%] |
| minimum cvar | -11.13% | 12.90% | -0.850 | -58.19% | 7.03 | 0 | [-1.93%, 10.48%] |

### short_window

Window `126`, rebalance every `21` days, cost `10.0` bps per unit of one-way turnover.

| Method | Ann. return | Ann. vol | Sharpe | Max DD | Turnover | Failures | 95% annualized mean-return diff vs EW |
|---|---:|---:|---:|---:|---:|---:|---:|
| equal weight | -14.48% | 15.58% | -0.925 | -68.55% | 1.30 | 0 | baseline |
| inverse volatility | -13.13% | 14.56% | -0.893 | -64.90% | 1.86 | 0 | [0.13%, 2.65%] |
| sample min variance | -8.71% | 12.27% | -0.680 | -56.85% | 6.28 | 0 | [0.79%, 11.54%] |
| oas min variance | -8.78% | 12.30% | -0.684 | -56.90% | 6.28 | 0 | [0.35%, 12.37%] |
| risk parity | -12.63% | 14.04% | -0.891 | -63.47% | 2.36 | 0 | [-0.14%, 4.09%] |
| minimum cvar | -9.55% | 12.92% | -0.712 | -59.41% | 12.13 | 0 | [-0.46%, 10.92%] |

### high_cost

Window `252`, rebalance every `21` days, cost `25.0` bps per unit of one-way turnover.

| Method | Ann. return | Ann. vol | Sharpe | Max DD | Turnover | Failures | 95% annualized mean-return diff vs EW |
|---|---:|---:|---:|---:|---:|---:|---:|
| equal weight | -15.16% | 16.12% | -0.939 | -68.61% | 1.25 | 0 | baseline |
| inverse volatility | -13.73% | 15.06% | -0.904 | -65.01% | 1.44 | 0 | [0.26%, 2.83%] |
| sample min variance | -9.82% | 12.61% | -0.756 | -57.50% | 3.39 | 0 | [0.35%, 11.41%] |
| oas min variance | -9.73% | 12.62% | -0.746 | -57.44% | 3.44 | 0 | [0.33%, 11.01%] |
| risk parity | -13.20% | 14.53% | -0.900 | -63.61% | 1.64 | 0 | [0.01%, 4.02%] |
| minimum cvar | -11.29% | 12.90% | -0.863 | -58.31% | 7.03 | 0 | [-1.20%, 10.01%] |

### low_frequency

Window `252`, rebalance every `63` days, cost `10.0` bps per unit of one-way turnover.

| Method | Ann. return | Ann. vol | Sharpe | Max DD | Turnover | Failures | 95% annualized mean-return diff vs EW |
|---|---:|---:|---:|---:|---:|---:|---:|
| equal weight | -15.05% | 16.10% | -0.931 | -68.39% | 0.72 | 0 | baseline |
| inverse volatility | -13.64% | 15.07% | -0.897 | -64.89% | 0.82 | 0 | [0.23%, 2.88%] |
| sample min variance | -9.56% | 12.65% | -0.731 | -58.18% | 1.79 | 0 | [0.55%, 11.46%] |
| oas min variance | -9.58% | 12.66% | -0.731 | -58.15% | 1.82 | 0 | [-0.39%, 10.88%] |
| risk parity | -13.14% | 14.54% | -0.895 | -63.55% | 0.89 | 0 | [-0.17%, 3.97%] |
| minimum cvar | -10.94% | 12.84% | -0.838 | -58.60% | 3.98 | 0 | [-1.45%, 10.17%] |

## Interpretation boundary

This experiment can reveal comparative behavior under a known synthetic stress process. It cannot establish that a method will outperform on future market data. Bootstrap intervals quantify resampling uncertainty conditional on this generated path; they do not include model risk from choosing the simulator itself.

## Retained artifacts

- `results.json`: complete configuration, environment, metrics, diagnostics, and uncertainty.
- `summary.csv`: flat review table.
- `base-cumulative-wealth.png`, `base-drawdowns.png`, `base-sharpe.png`: generated figures.
