# Limitations

1. **Synthetic model risk.** The path is stylized and cannot establish real-market performance.
2. **Single retained path.** Bootstrap resampling addresses local path uncertainty, not uncertainty over simulator families.
3. **Window stationarity assumption.** OAS and empirical scenarios treat each trailing window as exchangeable even when the process changes within it.
4. **Long-only simplification.** No leverage, shorting, financing, borrow availability, or margin.
5. **Linear transaction cost.** No spread state, market impact, queue position, or capacity model.
6. **No asset lifecycle.** No corporate actions, delistings, survivorship process, or currency conversion.
7. **CVaR scenario dependence.** The linear program sees only realized observations in the trailing window.
8. **Bootstrap interpretation.** Intervals depend on block length and are not a guarantee of out-of-sample superiority.
9. **Numerical optimization.** Risk parity is non-convex and can depend on initialization; failures are counted but global optimality is not claimed.
10. **No live trading.** There are no broker, exchange, or order-management integrations.
