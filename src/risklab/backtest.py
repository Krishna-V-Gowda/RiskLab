from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .allocators import allocate_all

FloatArray = NDArray[np.float64]
BoolArray = NDArray[np.bool_]


@dataclass(frozen=True)
class MethodResult:
    method: str
    net_returns: FloatArray
    gross_returns: FloatArray
    turnover: FloatArray
    cost: FloatArray
    end_of_day_weights: FloatArray
    target_weights: FloatArray
    rebalance_mask: BoolArray
    estimation_end: NDArray[np.int64]
    optimizer_failures: int


@dataclass(frozen=True)
class BacktestResult:
    methods: dict[str, MethodResult]
    start_index: int
    window: int
    rebalance_every: int
    transaction_cost_bps: float


def _validate_returns(returns: FloatArray, window: int, rebalance_every: int, transaction_cost_bps: float) -> FloatArray:
    matrix = np.asarray(returns, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] <= window or matrix.shape[1] < 1:
        raise ValueError("returns must be two-dimensional with more rows than window")
    if not np.isfinite(matrix).all():
        raise ValueError("returns must be finite")
    if window < 30:
        raise ValueError("window must be at least 30")
    if rebalance_every <= 0:
        raise ValueError("rebalance_every must be positive")
    if transaction_cost_bps < 0:
        raise ValueError("transaction_cost_bps must be non-negative")
    return matrix


def run_walk_forward(
    returns: FloatArray,
    *,
    window: int,
    rebalance_every: int,
    transaction_cost_bps: float,
    max_weight: float = 0.35,
    cvar_alpha: float = 0.95,
) -> BacktestResult:
    matrix = _validate_returns(returns, window, rebalance_every, transaction_cost_bps)
    n_days, n_assets = matrix.shape
    out_days = n_days - window
    method_names = (
        "equal_weight",
        "inverse_volatility",
        "sample_min_variance",
        "oas_min_variance",
        "risk_parity",
        "minimum_cvar",
    )

    current = {name: np.full(n_assets, 1.0 / n_assets) for name in method_names}
    gross = {name: np.zeros(out_days) for name in method_names}
    net = {name: np.zeros(out_days) for name in method_names}
    turnover = {name: np.zeros(out_days) for name in method_names}
    costs = {name: np.zeros(out_days) for name in method_names}
    end_weights = {name: np.zeros((out_days, n_assets)) for name in method_names}
    target_weights = {name: np.zeros((out_days, n_assets)) for name in method_names}
    failures = {name: 0 for name in method_names}
    rebalance_mask = np.zeros(out_days, dtype=bool)
    estimation_end = np.full(out_days, -1, dtype=np.int64)
    cost_rate = transaction_cost_bps / 10_000.0

    for offset, day in enumerate(range(window, n_days)):
        is_rebalance = offset == 0 or offset % rebalance_every == 0
        rebalance_mask[offset] = is_rebalance
        if is_rebalance:
            history = matrix[day - window : day]
            decisions = allocate_all(history, max_weight=max_weight, cvar_alpha=cvar_alpha)
            estimation_end[offset] = day
            for name in method_names:
                decision = decisions[name]
                if not decision.converged:
                    failures[name] += 1
                    proposed = current[name]
                else:
                    proposed = decision.weights
                if offset == 0:
                    one_way_turnover = 0.0  # initial formation is deliberately excluded
                else:
                    one_way_turnover = 0.5 * float(np.abs(proposed - current[name]).sum())
                current[name] = proposed.copy()
                turnover[name][offset] = one_way_turnover
                costs[name][offset] = one_way_turnover * cost_rate

        daily = matrix[day]
        for name in method_names:
            target_weights[name][offset] = current[name]
            gross_return = float(current[name] @ daily)
            gross[name][offset] = gross_return
            net[name][offset] = gross_return - costs[name][offset]
            components = current[name] * (1.0 + daily)
            total = float(components.sum())
            if total <= 0 or not np.isfinite(total):
                raise RuntimeError("portfolio wealth became non-positive or non-finite")
            current[name] = components / total
            end_weights[name][offset] = current[name]

    results = {
        name: MethodResult(
            method=name,
            net_returns=net[name],
            gross_returns=gross[name],
            turnover=turnover[name],
            cost=costs[name],
            end_of_day_weights=end_weights[name],
            target_weights=target_weights[name],
            rebalance_mask=rebalance_mask.copy(),
            estimation_end=estimation_end.copy(),
            optimizer_failures=failures[name],
        )
        for name in method_names
    }
    return BacktestResult(results, window, window, rebalance_every, transaction_cost_bps)
