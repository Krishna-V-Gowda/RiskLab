from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def _series(values: FloatArray) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("values must be a non-empty one-dimensional array")
    if not np.isfinite(array).all() or (array <= -1.0).any():
        raise ValueError("returns must be finite and greater than -1")
    return array


def annualized_return(returns: FloatArray, annualization: int = 252) -> float:
    values = _series(returns)
    wealth = float(np.prod(1.0 + values))
    return float(wealth ** (annualization / values.size) - 1.0)


def annualized_volatility(returns: FloatArray, annualization: int = 252) -> float:
    values = _series(returns)
    if values.size < 2:
        return 0.0
    return float(values.std(ddof=1) * math.sqrt(annualization))


def sharpe_ratio(returns: FloatArray, annualization: int = 252) -> float:
    values = _series(returns)
    std = float(values.std(ddof=1)) if values.size > 1 else 0.0
    if std <= np.finfo(np.float64).eps:
        return 0.0
    return float(values.mean() / std * math.sqrt(annualization))


def sortino_ratio(returns: FloatArray, annualization: int = 252) -> float:
    values = _series(returns)
    downside = np.minimum(values, 0.0)
    downside_deviation = float(np.sqrt(np.mean(downside * downside)))
    if downside_deviation <= np.finfo(np.float64).eps:
        return 0.0
    return float(values.mean() / downside_deviation * math.sqrt(annualization))


def max_drawdown(returns: FloatArray) -> float:
    values = _series(returns)
    wealth = np.concatenate(([1.0], np.cumprod(1.0 + values)))
    peaks = np.maximum.accumulate(wealth)
    drawdowns = wealth / peaks - 1.0
    return float(drawdowns.min())


def expected_shortfall(returns: FloatArray, level: float = 0.95) -> float:
    values = _series(returns)
    if not 0 < level < 1:
        raise ValueError("level must be in (0, 1)")
    tail_count = max(1, int(math.ceil((1.0 - level) * values.size)))
    worst = np.partition(values, tail_count - 1)[:tail_count]
    return float(-worst.mean())


def summarize(
    net_returns: FloatArray,
    gross_returns: FloatArray,
    turnover: FloatArray,
    annualization: int = 252,
) -> dict[str, float]:
    net = _series(net_returns)
    gross = _series(gross_returns)
    turn = np.asarray(turnover, dtype=np.float64)
    if turn.shape != net.shape or not np.isfinite(turn).all() or (turn < 0).any():
        raise ValueError("turnover must be finite, non-negative, and aligned")
    return {
        "annualized_return": annualized_return(net, annualization),
        "annualized_volatility": annualized_volatility(net, annualization),
        "sharpe": sharpe_ratio(net, annualization),
        "sortino": sortino_ratio(net, annualization),
        "max_drawdown": max_drawdown(net),
        "expected_shortfall_95": expected_shortfall(net, 0.95),
        "ending_wealth": float(np.prod(1.0 + net)),
        "total_one_way_turnover": float(turn.sum()),
        "cost_drag": float(gross.sum() - net.sum()),
        "mean_daily_return": float(net.mean()),
    }
