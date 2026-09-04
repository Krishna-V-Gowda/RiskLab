from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import ExperimentConfig, default_scenarios
from .experiment import run_experiment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="risklab", description="Run controlled allocation-robustness experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run the deterministic experiment")
    run.add_argument("--output-dir", default="evidence/final")
    run.add_argument("--days", type=int, default=1800)
    run.add_argument("--assets", type=int, default=8)
    run.add_argument("--seed", type=int, default=20260903)
    run.add_argument("--bootstrap-resamples", type=int, default=500)
    run.add_argument("--scenario-limit", type=int, default=4, choices=(1, 2, 3, 4))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        config = ExperimentConfig(
            n_assets=args.assets,
            n_days=args.days,
            seed=args.seed,
            bootstrap_resamples=args.bootstrap_resamples,
            block_length=min(21, args.days),
        )
        scenarios = default_scenarios(config.n_days)[: args.scenario_limit]
        payload = run_experiment(Path(args.output_dir), config=config, scenarios=scenarios)
        print(json.dumps({
            "output_dir": str(Path(args.output_dir).resolve()),
            "returns_sha256": payload["market"]["returns_sha256"],
            "scenarios": len(payload["scenarios"]),
            "runtime_seconds": payload["runtime_seconds"],
        }, indent=2))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
