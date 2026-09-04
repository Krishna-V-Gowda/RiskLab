import unittest

import numpy as np

from risklab.backtest import run_walk_forward
from risklab.simulate import simulate_market


class BacktestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.returns = simulate_market(220, 5, 42).returns

    def test_shapes_weights_and_rebalance_count(self):
        result = run_walk_forward(self.returns, window=60, rebalance_every=20, transaction_cost_bps=10)
        for method in result.methods.values():
            self.assertEqual(method.net_returns.shape, (160,))
            self.assertEqual(method.end_of_day_weights.shape, (160, 5))
            np.testing.assert_allclose(method.end_of_day_weights.sum(axis=1), 1.0, atol=1e-10)
            self.assertEqual(int(method.rebalance_mask.sum()), 8)

    def test_costs_never_improve_returns(self):
        result = run_walk_forward(self.returns, window=60, rebalance_every=20, transaction_cost_bps=25)
        for method in result.methods.values():
            self.assertTrue(np.all(method.net_returns <= method.gross_returns + 1e-15))
            np.testing.assert_allclose(method.gross_returns - method.net_returns, method.cost)

    def test_no_future_leakage(self):
        original = run_walk_forward(self.returns, window=60, rebalance_every=20, transaction_cost_bps=10)
        mutated = self.returns.copy()
        mutated[160:] *= -7.0
        changed = run_walk_forward(mutated, window=60, rebalance_every=20, transaction_cost_bps=10)
        # Target weights selected before day 160 must be bit-identical.
        out_cutoff = 160 - 60
        for name in original.methods:
            np.testing.assert_array_equal(
                original.methods[name].target_weights[:out_cutoff],
                changed.methods[name].target_weights[:out_cutoff],
            )

    def test_deterministic(self):
        first = run_walk_forward(self.returns, window=60, rebalance_every=20, transaction_cost_bps=10)
        second = run_walk_forward(self.returns, window=60, rebalance_every=20, transaction_cost_bps=10)
        for name in first.methods:
            np.testing.assert_array_equal(first.methods[name].net_returns, second.methods[name].net_returns)

    def test_estimation_window_ends_at_decision_day(self):
        result = run_walk_forward(self.returns, window=60, rebalance_every=20, transaction_cost_bps=0)
        ends = result.methods["equal_weight"].estimation_end
        self.assertEqual(ends[0], 60)
        self.assertEqual(ends[20], 80)
        self.assertTrue((ends[~result.methods["equal_weight"].rebalance_mask] == -1).all())


if __name__ == "__main__":
    unittest.main()
