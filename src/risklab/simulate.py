from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class RegimeRecord:
    name: str
    start: int
    end: int


@dataclass(frozen=True)
class SimulatedMarket:
    returns: FloatArray
    asset_names: tuple[str, ...]
    regimes: tuple[RegimeRecord, ...]
    regime_by_day: tuple[str, ...]
    seed: int


_REGIME_NAMES = ("calm", "correlation_shock", "recovery", "inflation_volatility")


def _correlation_matrix(base_corr: float, n_factors: int = 3) -> FloatArray:
    corr = np.full((n_factors, n_factors), base_corr, dtype=np.float64)
    np.fill_diagonal(corr, 1.0)
    return corr


def _multivariate_t(
    rng: np.random.Generator,
    n: int,
    covariance: FloatArray,
    degrees_of_freedom: float,
) -> FloatArray:
    z = rng.multivariate_normal(np.zeros(covariance.shape[0]), covariance, size=n)
    scale = np.sqrt(degrees_of_freedom / rng.chisquare(degrees_of_freedom, size=n))
    return z * scale[:, None]


def _boundaries(n_days: int) -> list[tuple[int, int]]:
    cuts = [0, n_days // 4, n_days // 2, (3 * n_days) // 4, n_days]
    return list(zip(cuts[:-1], cuts[1:], strict=True))


def simulate_market(n_days: int = 1800, n_assets: int = 8, seed: int = 20260903) -> SimulatedMarket:
    """Create deterministic, heavy-tailed returns with known regime changes.

    This is a controlled stress laboratory, not a calibrated market forecast.
    """
    if n_days < 80:
        raise ValueError("n_days must be at least 80")
    if n_assets < 3:
        raise ValueError("n_assets must be at least 3")

    rng = np.random.default_rng(seed)
    loadings = rng.normal(0.55, 0.20, size=(n_assets, 3))
    loadings[:, 1] *= np.linspace(-0.8, 0.9, n_assets)
    loadings[:, 2] *= np.where(np.arange(n_assets) % 2 == 0, 1.0, -0.7)

    regime_specs = (
        # daily factor vols, average correlation, daily drift, idiosyncratic scale, df
        (np.array([0.0060, 0.0042, 0.0035]), 0.10, 0.00028, 0.0040, 8.0),
        (np.array([0.0170, 0.0120, 0.0100]), 0.72, -0.00075, 0.0085, 4.5),
        (np.array([0.0090, 0.0065, 0.0055]), 0.30, 0.00055, 0.0055, 6.0),
        (np.array([0.0130, 0.0090, 0.0120]), 0.42, 0.00005, 0.0070, 5.0),
    )

    blocks: list[FloatArray] = []
    labels: list[str] = []
    records: list[RegimeRecord] = []
    asset_drift_tilt = np.linspace(-0.00010, 0.00012, n_assets)

    for name, (start, end), spec in zip(_REGIME_NAMES, _boundaries(n_days), regime_specs, strict=True):
        vols, corr_level, common_drift, idio_scale, df = spec
        corr = _correlation_matrix(corr_level)
        factor_cov = np.diag(vols) @ corr @ np.diag(vols)
        factor_returns = _multivariate_t(rng, end - start, factor_cov, df)
        idiosyncratic = rng.standard_t(df + 1.0, size=(end - start, n_assets)) * idio_scale
        returns = factor_returns @ loadings.T + idiosyncratic
        returns += common_drift + asset_drift_tilt

        if name == "correlation_shock":
            shock_days = rng.choice(end - start, size=max(2, (end - start) // 35), replace=False)
            returns[shock_days] -= rng.uniform(0.025, 0.070, size=(len(shock_days), 1))
        elif name == "inflation_volatility":
            returns[:, ::2] += 0.00018
            returns[:, 1::2] -= 0.00012

        returns = np.clip(returns, -0.30, 0.30).astype(np.float64, copy=False)
        blocks.append(returns)
        labels.extend([name] * (end - start))
        records.append(RegimeRecord(name, start, end))

    matrix = np.vstack(blocks)
    if matrix.shape != (n_days, n_assets) or not np.isfinite(matrix).all():
        raise RuntimeError("simulator produced an invalid matrix")

    return SimulatedMarket(
        returns=matrix,
        asset_names=tuple(f"Asset_{index + 1:02d}" for index in range(n_assets)),
        regimes=tuple(records),
        regime_by_day=tuple(labels),
        seed=seed,
    )
