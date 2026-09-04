import unittest

import numpy as np

from risklab.bootstrap import circular_moving_block_indices, paired_block_bootstrap_difference


class BootstrapTests(unittest.TestCase):
    def test_indices_have_expected_shape_and_range(self):
        indices = circular_moving_block_indices(17, 5, np.random.default_rng(3))
        self.assertEqual(indices.shape, (17,))
        self.assertGreaterEqual(int(indices.min()), 0)
        self.assertLess(int(indices.max()), 17)

    def test_identical_series_have_zero_interval(self):
        values = np.linspace(-0.01, 0.01, 80)
        result = paired_block_bootstrap_difference(values, values, resamples=50, block_length=5, seed=9)
        self.assertAlmostEqual(result.observed_annualized_difference, 0)
        self.assertAlmostEqual(result.lower_95, 0)
        self.assertAlmostEqual(result.upper_95, 0)

    def test_deterministic(self):
        rng = np.random.default_rng(8)
        a = rng.normal(size=100)
        b = rng.normal(size=100)
        first = paired_block_bootstrap_difference(a, b, resamples=100, block_length=7, seed=22)
        second = paired_block_bootstrap_difference(a, b, resamples=100, block_length=7, seed=22)
        self.assertEqual(first, second)
        self.assertLessEqual(first.lower_95, first.upper_95)


if __name__ == "__main__":
    unittest.main()
