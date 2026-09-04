import unittest

import numpy as np

from risklab.estimators import empirical_covariance, nearest_psd, oas_covariance


class EstimatorTests(unittest.TestCase):
    def setUp(self):
        self.x = np.random.default_rng(12).normal(size=(120, 5))

    def test_empirical_is_symmetric_psd(self):
        result = empirical_covariance(self.x)
        np.testing.assert_allclose(result.covariance, result.covariance.T, atol=1e-12)
        self.assertGreater(np.linalg.eigvalsh(result.covariance).min(), 0)

    def test_oas_has_valid_shrinkage(self):
        result = oas_covariance(self.x)
        self.assertGreaterEqual(result.shrinkage, 0)
        self.assertLessEqual(result.shrinkage, 1)
        self.assertTrue(np.isfinite(result.condition_number))

    def test_oas_reduces_pathological_condition_number(self):
        rng = np.random.default_rng(9)
        base = rng.normal(size=(30, 1))
        x = np.hstack([base + 1e-5 * rng.normal(size=(30, 1)) for _ in range(8)])
        empirical = empirical_covariance(x)
        oas = oas_covariance(x)
        self.assertLess(oas.condition_number, empirical.condition_number)

    def test_nearest_psd_repairs_negative_eigenvalue(self):
        repaired = nearest_psd(np.array([[1.0, 2.0], [2.0, 1.0]]))
        self.assertGreater(np.linalg.eigvalsh(repaired).min(), 0)

    def test_rejects_nonfinite(self):
        x = self.x.copy()
        x[0, 0] = np.nan
        with self.assertRaises(ValueError):
            oas_covariance(x)


if __name__ == "__main__":
    unittest.main()
