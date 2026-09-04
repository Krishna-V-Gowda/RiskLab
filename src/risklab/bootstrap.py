from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class BootstrapDifference:
    observed_annualized_difference: float
    lower_95: float
    upper_95: float
    probability_positive: float
    resamples: int
    block_length: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "observed_annualized_difference": self.observed_annualized_difference,
            "lower_95": self.lower_95,
            "upper_95": self.upper_95,
            "probability_positive": self.probability_positive,
            "resamples": self.resamples,
            "block_length": self.block_length,
        }


def circular_moving_block_indices(
    n_observations: int,
    block_length: int,
    rng: np.random.Generator,
) -> NDArray[np.int64]:
    if n_observations <= 0:
        raise ValueError("n_observations must be positive")
    if not 1 <= block_length <= n_observations:
        raise ValueError("block_length must be in [1, n_observations]")
    n_blocks = int(np.ceil(n_observations / block_length))
    starts = rng.integers(0, n_observations, size=n_blocks)
    offsets = np.arange(block_length)
    indices = ((starts[:, None] + offsets[None, :]) % n_observations).reshape(-1)
    return indices[:n_observations].astype(np.int64, copy=False)


def paired_block_bootstrap_difference(
    candidate_returns: FloatArray,
    baseline_returns: FloatArray,
    *,
    resamples: int,
    block_length: int,
    seed: int,
    annualization: int = 252,
) -> BootstrapDifference:
    candidate = np.asarray(candidate_returns, dtype=np.float64)
    baseline = np.asarray(baseline_returns, dtype=np.float64)
    if candidate.ndim != 1 or candidate.shape != baseline.shape or candidate.size == 0:
        raise ValueError("candidate and baseline must be aligned non-empty series")
    if not np.isfinite(candidate).all() or not np.isfinite(baseline).all():
        raise ValueError("returns must be finite")
    if resamples <= 0:
        raise ValueError("resamples must be positive")
    difference = candidate - baseline
    rng = np.random.default_rng(seed)
    draws = np.empty(resamples, dtype=np.float64)
    for index in range(resamples):
        selected = circular_moving_block_indices(difference.size, block_length, rng)
        draws[index] = float(difference[selected].mean() * annualization)
    observed = float(difference.mean() * annualization)
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return BootstrapDifference(
        observed,
        float(lower),
        float(upper),
        float(np.mean(draws > 0.0)),
        resamples,
        block_length,
    )
