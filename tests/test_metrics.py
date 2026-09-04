import unittest

import numpy as np

from risklab.metrics import expected_shortfall, max_drawdown, summarize


class MetricTests(unittest.TestCase):
    def test_max_drawdown_includes_initial_wealth(self):
        self.assertAlmostEqual(max_drawdown(np.array([0.10, -0.20, 0.05])), -0.20)

    def test_expected_shortfall_uses_worst_tail_count(self):
        values = np.array([-0.10, -0.05, 0.01, 0.02])
        self.assertAlmostEqual(expected_shortfall(values, 0.50), 0.075)

    def test_cost_drag_and_turnover(self):
        gross = np.array([0.01, 0.02, -0.01])
        net = gross - np.array([0.001, 0.0, 0.002])
        summary = summarize(net, gross, np.array([0.5, 0.0, 1.0]))
        self.assertAlmostEqual(summary["cost_drag"], 0.003)
        self.assertAlmostEqual(summary["total_one_way_turnover"], 1.5)

    def test_invalid_return_is_rejected(self):
        with self.assertRaises(ValueError):
            max_drawdown(np.array([0.1, -1.0]))


if __name__ == "__main__":
    unittest.main()
