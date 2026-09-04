import unittest

import numpy as np

from risklab.simulate import simulate_market


class SimulationTests(unittest.TestCase):
    def test_deterministic(self):
        first = simulate_market(400, 6, 7)
        second = simulate_market(400, 6, 7)
        np.testing.assert_array_equal(first.returns, second.returns)

    def test_seed_changes_path(self):
        first = simulate_market(400, 6, 7)
        second = simulate_market(400, 6, 8)
        self.assertFalse(np.array_equal(first.returns, second.returns))

    def test_shape_finiteness_and_regimes(self):
        market = simulate_market(401, 5, 11)
        self.assertEqual(market.returns.shape, (401, 5))
        self.assertTrue(np.isfinite(market.returns).all())
        self.assertEqual(len(market.regime_by_day), 401)
        self.assertEqual({r.name for r in market.regimes}, set(market.regime_by_day))
        self.assertEqual(market.regimes[0].start, 0)
        self.assertEqual(market.regimes[-1].end, 401)

    def test_rejects_tiny_inputs(self):
        with self.assertRaises(ValueError):
            simulate_market(20, 8, 1)
        with self.assertRaises(ValueError):
            simulate_market(100, 2, 1)


if __name__ == "__main__":
    unittest.main()
