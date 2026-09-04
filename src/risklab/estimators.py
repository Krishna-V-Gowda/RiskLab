from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class CovarianceEstimate:
    covariance: FloatArray
    shrinkage: float
    condition_number: float


def _validate_observations(observations: FloatArray) -> FloatArray:
    x = np.asarray(observations, dtype=np.float64)
    if x.ndim != 2 or x.shape[0] < 2 or x.shape[1] < 1:
        raise ValueError("observations must have shape (n_samples >= 2, n_features >= 1)")
    if not np.isfinite(x).all():
        raise ValueError("observations must be finite")
    return x


def nearest_psd(matrix: FloatArray, floor: float = 1e-10) -> FloatArray:
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("matrix must be square")
    symmetric = (matrix + matrix.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    scale = max(float(np.max(np.abs(eigenvalues))), 1.0)
    clipped = np.maximum(eigenvalues, floor * scale)
    repaired = (eigenvectors * clipped) @ eigenvectors.T
    return (repaired + repaired.T) / 2.0


def _condition_number(covariance: FloatArray) -> float:
    values = np.linalg.eigvalsh(covariance)
    positive = values[values > np.finfo(np.float64).eps]
    if positive.size == 0:
        return float("inf")
    return float(positive.max() / positive.min())


def empirical_covariance(observations: FloatArray) -> CovarianceEstimate:
    x = _validate_observations(observations)
    covariance = np.cov(x, rowvar=False, ddof=1)
    covariance = np.atleast_2d(covariance).astype(np.float64)
    covariance = nearest_psd(covariance)
    return CovarianceEstimate(covariance, 0.0, _condition_number(covariance))


def oas_covariance(observations: FloatArray) -> CovarianceEstimate:
    """Oracle Approximating Shrinkage covariance.

    The implementation follows the finite-sample OAS coefficient used for a
    covariance target of ``mu * I``. The covariance uses the maximum-likelihood
    ``1/n`` normalization required by that derivation.
    """
    x = _validate_observations(observations)
    centered = x - x.mean(axis=0, keepdims=True)
    n_samples, n_features = centered.shape
    empirical = (centered.T @ centered) / float(n_samples)
    mu = float(np.trace(empirical) / n_features)
    alpha = float(np.mean(empirical * empirical))
    denominator = (n_samples + 1.0) * (alpha - (mu * mu) / n_features)
    if denominator <= np.finfo(np.float64).eps:
        shrinkage = 1.0
    else:
        shrinkage = min((alpha + mu * mu) / denominator, 1.0)
    target = mu * np.eye(n_features, dtype=np.float64)
    covariance = (1.0 - shrinkage) * empirical + shrinkage * target
    covariance = nearest_psd(covariance)
    return CovarianceEstimate(covariance, float(shrinkage), _condition_number(covariance))
