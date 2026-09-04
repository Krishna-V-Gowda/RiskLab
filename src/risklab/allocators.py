from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import linprog, minimize

from .estimators import empirical_covariance, nearest_psd, oas_covariance

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class Allocation:
    weights: FloatArray
    converged: bool
    message: str
    diagnostics: dict[str, float]


def _effective_cap(n_assets: int, max_weight: float) -> float:
    if not 0 < max_weight <= 1:
        raise ValueError("max_weight must be in (0, 1]")
    return max(max_weight, (1.0 / n_assets) + 1e-12)


def _validated_covariance(covariance: FloatArray) -> FloatArray:
    cov = np.asarray(covariance, dtype=np.float64)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1] or cov.shape[0] == 0:
        raise ValueError("covariance must be a non-empty square matrix")
    if not np.isfinite(cov).all():
        raise ValueError("covariance must be finite")
    return nearest_psd(cov)


def _normalize(weights: FloatArray) -> FloatArray:
    weights = np.asarray(weights, dtype=np.float64)
    total = float(weights.sum())
    if not np.isfinite(weights).all() or total <= 0:
        raise ValueError("weights must be finite with positive total")
    normalized = weights / total
    if (normalized < -1e-9).any():
        raise ValueError("weights must be long-only")
    return np.maximum(normalized, 0.0) / np.maximum(normalized, 0.0).sum()


def equal_weight(n_assets: int) -> Allocation:
    if n_assets <= 0:
        raise ValueError("n_assets must be positive")
    weights = np.full(n_assets, 1.0 / n_assets, dtype=np.float64)
    return Allocation(weights, True, "closed form", {})


def inverse_volatility(covariance: FloatArray) -> Allocation:
    cov = _validated_covariance(covariance)
    volatility = np.sqrt(np.maximum(np.diag(cov), np.finfo(np.float64).eps))
    weights = _normalize(1.0 / volatility)
    return Allocation(weights, True, "closed form", {})


def minimum_variance(covariance: FloatArray, max_weight: float = 0.35) -> Allocation:
    cov = _validated_covariance(covariance)
    n_assets = cov.shape[0]
    cap = _effective_cap(n_assets, max_weight)
    initial = np.full(n_assets, 1.0 / n_assets)
    result = minimize(
        lambda w: float(w @ cov @ w),
        initial,
        method="SLSQP",
        jac=lambda w: 2.0 * (cov @ w),
        bounds=[(0.0, cap)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: float(w.sum() - 1.0), "jac": lambda w: np.ones_like(w)},
        options={"ftol": 1e-12, "maxiter": 500},
    )
    if not result.success:
        return Allocation(initial, False, str(result.message), {"objective": float(initial @ cov @ initial)})
    weights = _normalize(result.x)
    return Allocation(weights, True, str(result.message), {"objective": float(weights @ cov @ weights)})


def risk_parity(covariance: FloatArray, max_weight: float = 0.35) -> Allocation:
    cov = _validated_covariance(covariance)
    n_assets = cov.shape[0]
    cap = _effective_cap(n_assets, max_weight)
    initial = np.full(n_assets, 1.0 / n_assets)

    def objective(weights: FloatArray) -> float:
        marginal = cov @ weights
        variance = max(float(weights @ marginal), np.finfo(np.float64).eps)
        contributions = weights * marginal
        target = variance / n_assets
        return float(np.sum((contributions - target) ** 2) / (variance * variance))

    result = minimize(
        objective,
        initial,
        method="SLSQP",
        bounds=[(1e-10, cap)] * n_assets,
        constraints={"type": "eq", "fun": lambda w: float(w.sum() - 1.0)},
        options={"ftol": 1e-13, "maxiter": 1000},
    )
    if not result.success:
        return Allocation(initial, False, str(result.message), {"objective": objective(initial)})
    weights = _normalize(result.x)
    return Allocation(weights, True, str(result.message), {"objective": objective(weights)})


def minimum_cvar(
    observations: FloatArray,
    alpha: float = 0.95,
    max_weight: float = 0.35,
) -> Allocation:
    returns = np.asarray(observations, dtype=np.float64)
    if returns.ndim != 2 or returns.shape[0] < 2 or returns.shape[1] < 1:
        raise ValueError("observations must be a two-dimensional return matrix")
    if not np.isfinite(returns).all():
        raise ValueError("observations must be finite")
    if not 0.5 < alpha < 1.0:
        raise ValueError("alpha must be between 0.5 and 1")

    n_scenarios, n_assets = returns.shape
    cap = _effective_cap(n_assets, max_weight)
    # Decision vector: [weights (n), VaR threshold zeta (1), excess losses u (T)].
    objective = np.concatenate(
        [
            np.zeros(n_assets),
            np.array([1.0]),
            np.full(n_scenarios, 1.0 / ((1.0 - alpha) * n_scenarios)),
        ]
    )
    a_ub = np.zeros((n_scenarios, n_assets + 1 + n_scenarios), dtype=np.float64)
    a_ub[:, :n_assets] = -returns
    a_ub[:, n_assets] = -1.0
    a_ub[np.arange(n_scenarios), n_assets + 1 + np.arange(n_scenarios)] = -1.0
    b_ub = np.zeros(n_scenarios)
    a_eq = np.zeros((1, n_assets + 1 + n_scenarios), dtype=np.float64)
    a_eq[0, :n_assets] = 1.0
    b_eq = np.array([1.0])
    bounds = [(0.0, cap)] * n_assets + [(None, None)] + [(0.0, None)] * n_scenarios

    result = linprog(objective, A_ub=a_ub, b_ub=b_ub, A_eq=a_eq, b_eq=b_eq, bounds=bounds, method="highs")
    initial = np.full(n_assets, 1.0 / n_assets)
    if not result.success:
        return Allocation(initial, False, str(result.message), {"objective": float("nan")})
    weights = _normalize(result.x[:n_assets])
    return Allocation(weights, True, str(result.message), {"objective": float(result.fun)})


Allocator = Callable[[FloatArray], Allocation]


def allocate_all(
    observations: FloatArray,
    *,
    max_weight: float = 0.35,
    cvar_alpha: float = 0.95,
) -> dict[str, Allocation]:
    empirical = empirical_covariance(observations)
    oas = oas_covariance(observations)
    return {
        "equal_weight": equal_weight(observations.shape[1]),
        "inverse_volatility": inverse_volatility(empirical.covariance),
        "sample_min_variance": minimum_variance(empirical.covariance, max_weight),
        "oas_min_variance": minimum_variance(oas.covariance, max_weight),
        "risk_parity": risk_parity(oas.covariance, max_weight),
        "minimum_cvar": minimum_cvar(observations, cvar_alpha, max_weight),
    }
