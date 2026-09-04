import unittest

import numpy as np

from risklab.allocators import (
    equal_weight,
    inverse_volatility,
    minimum_cvar,
    minimum_variance,
    risk_parity,
)


class AllocatorTests(unittest.TestCase):
    def assert_valid(self, weights):
        self.assertAlmostEqual(float(weights.sum()), 1.0, places=8)
        self.assertGreaterEqual(float(weights.min()), -1e-10)
        self.assertTrue(np.isfinite(weights).all())

    def test_equal_weight(self):
        allocation = equal_weight(4)
        np.testing.assert_allclose(allocation.weights, 0.25)

    def test_inverse_volatility_prefers_lower_volatility(self):
        allocation = inverse_volatility(np.diag([1.0, 4.0, 9.0]))
        self.assert_valid(allocation.weights)
        self.assertGreater(allocation.weights[0], allocation.weights[1])
        self.assertGreater(allocation.weights[1], allocation.weights[2])

    def test_minimum_variance_improves_diagonal_objective(self):
        covariance = np.diag([0.01, 0.04, 0.09])
        allocation = minimum_variance(covariance, max_weight=0.8)
        self.assertTrue(allocation.converged)
        self.assert_valid(allocation.weights)
        equal = np.full(3, 1 / 3)
        self.assertLess(float(allocation.weights @ covariance @ allocation.weights), float(equal @ covariance @ equal))

    def test_risk_parity_equalizes_diagonal_risk_contributions(self):
        covariance = np.diag([0.01, 0.04, 0.09, 0.16])
        allocation = risk_parity(covariance, max_weight=0.8)
        self.assertTrue(allocation.converged)
        marginal = covariance @ allocation.weights
        contributions = allocation.weights * marginal
        self.assertLess(float(np.std(contributions) / np.mean(contributions)), 1e-3)

    def test_cvar_linear_program_is_feasible_for_two_assets(self):
        rng = np.random.default_rng(5)
        returns = rng.normal(0, [0.01, 0.03], size=(200, 2))
        allocation = minimum_cvar(returns, alpha=0.9, max_weight=0.45)
        self.assertTrue(allocation.converged)
        self.assert_valid(allocation.weights)

    def test_cap_is_respected_when_feasible(self):
        covariance = np.diag([0.001, 1.0, 1.0, 1.0])
        allocation = minimum_variance(covariance, max_weight=0.4)
        self.assertLessEqual(float(allocation.weights.max()), 0.4000001)

    def test_cvar_rejects_invalid_alpha(self):
        with self.assertRaises(ValueError):
            minimum_cvar(np.ones((20, 3)), alpha=1.0)


if __name__ == "__main__":
    unittest.main()
