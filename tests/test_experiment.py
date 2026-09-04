import json
import tempfile
import unittest
from pathlib import Path

from risklab.config import ExperimentConfig, default_scenarios
from risklab.experiment import run_experiment


class ExperimentTests(unittest.TestCase):
    def test_reduced_end_to_end_and_semantic_determinism(self):
        config = ExperimentConfig(n_assets=4, n_days=260, seed=77, bootstrap_resamples=20, block_length=5, max_weight=0.6)
        scenarios = default_scenarios(config.n_days)[:1]
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = run_experiment(first_dir, config=config, scenarios=scenarios)
            second = run_experiment(second_dir, config=config, scenarios=scenarios)
            for payload in (first, second):
                payload.pop("runtime_seconds")
                payload.pop("environment")
            self.assertEqual(first, second)
            for filename in ("results.json", "summary.csv", "report.md", "base-cumulative-wealth.png", "base-drawdowns.png", "base-sharpe.png"):
                self.assertTrue((Path(first_dir) / filename).is_file(), filename)
            parsed = json.loads((Path(first_dir) / "results.json").read_text())
            self.assertTrue(parsed["market"]["synthetic"])


if __name__ == "__main__":
    unittest.main()
