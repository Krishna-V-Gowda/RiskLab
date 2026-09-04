from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .backtest import BacktestResult, run_walk_forward
from .bootstrap import paired_block_bootstrap_difference
from .config import ExperimentConfig, Scenario, default_scenarios
from .estimators import empirical_covariance, oas_covariance
from .metrics import summarize
from .simulate import SimulatedMarket, simulate_market


def _sha256_array(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array.astype("<f8", copy=False))
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


def _runtime_environment() -> dict[str, str]:
    import scipy
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
        "platform": platform.platform(),
        "executable": sys.executable,
    }


def _scenario_result(
    market: SimulatedMarket,
    config: ExperimentConfig,
    scenario: Scenario,
    scenario_index: int,
) -> tuple[dict[str, Any], BacktestResult]:
    result = run_walk_forward(
        market.returns,
        window=scenario.window,
        rebalance_every=scenario.rebalance_every,
        transaction_cost_bps=scenario.transaction_cost_bps,
        max_weight=config.max_weight,
        cvar_alpha=config.cvar_alpha,
    )
    baseline = result.methods["equal_weight"].net_returns
    methods: dict[str, Any] = {}
    for method_index, (name, method) in enumerate(result.methods.items()):
        metrics = summarize(method.net_returns, method.gross_returns, method.turnover, config.annualization)
        bootstrap = None
        if name != "equal_weight":
            bootstrap = paired_block_bootstrap_difference(
                method.net_returns,
                baseline,
                resamples=config.bootstrap_resamples,
                block_length=min(config.block_length, method.net_returns.size),
                seed=config.seed + 1000 * (scenario_index + 1) + method_index,
                annualization=config.annualization,
            ).to_dict()
        methods[name] = {
            "metrics": metrics,
            "optimizer_failures": method.optimizer_failures,
            "rebalance_count": int(method.rebalance_mask.sum()),
            "bootstrap_vs_equal_weight": bootstrap,
        }
    return {
        "scenario": scenario.to_dict(),
        "methods": methods,
    }, result


def _covariance_diagnostics(market: SimulatedMarket, window: int) -> dict[str, float]:
    sample = market.returns[:window]
    empirical = empirical_covariance(sample)
    oas = oas_covariance(sample)
    return {
        "empirical_condition_number": empirical.condition_number,
        "oas_condition_number": oas.condition_number,
        "oas_shrinkage": oas.shrinkage,
        "condition_number_ratio_empirical_to_oas": empirical.condition_number / oas.condition_number,
    }


def _write_csv(path: Path, scenarios: list[dict[str, Any]]) -> None:
    fields = [
        "scenario", "method", "annualized_return", "annualized_volatility", "sharpe", "sortino",
        "max_drawdown", "expected_shortfall_95", "ending_wealth", "total_one_way_turnover",
        "cost_drag", "optimizer_failures", "bootstrap_lower_95", "bootstrap_upper_95",
        "bootstrap_probability_positive",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for scenario in scenarios:
            for method, entry in scenario["methods"].items():
                metrics = entry["metrics"]
                bootstrap = entry["bootstrap_vs_equal_weight"] or {}
                writer.writerow({
                    "scenario": scenario["scenario"]["name"],
                    "method": method,
                    **{key: metrics[key] for key in fields if key in metrics},
                    "optimizer_failures": entry["optimizer_failures"],
                    "bootstrap_lower_95": bootstrap.get("lower_95", ""),
                    "bootstrap_upper_95": bootstrap.get("upper_95", ""),
                    "bootstrap_probability_positive": bootstrap.get("probability_positive", ""),
                })


def _plot_base(output: Path, market: SimulatedMarket, base: BacktestResult, annualization: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    x = np.arange(base.methods["equal_weight"].net_returns.size)

    fig, ax = plt.subplots(figsize=(10, 5.6))
    for name, method in base.methods.items():
        wealth = np.cumprod(1.0 + method.net_returns)
        ax.plot(x, wealth, label=name.replace("_", " "))
    for record in market.regimes[1:]:
        boundary = record.start - base.start_index
        if 0 < boundary < x.size:
            ax.axvline(boundary, linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_title("Base scenario: net cumulative wealth on controlled regimes")
    ax.set_xlabel("out-of-sample day")
    ax.set_ylabel("wealth, initial = 1")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output / "base-cumulative-wealth.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5.6))
    for name, method in base.methods.items():
        wealth = np.concatenate(([1.0], np.cumprod(1.0 + method.net_returns)))
        drawdown = wealth / np.maximum.accumulate(wealth) - 1.0
        ax.plot(np.arange(drawdown.size), drawdown, label=name.replace("_", " "))
    ax.set_title("Base scenario: drawdown paths")
    ax.set_xlabel("out-of-sample day")
    ax.set_ylabel("drawdown")
    ax.legend(ncol=2, fontsize=8)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(output / "base-drawdowns.png", dpi=180)
    plt.close(fig)

    labels = list(base.methods)
    sharpes = [summarize(m.net_returns, m.gross_returns, m.turnover, annualization)["sharpe"] for m in base.methods.values()]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.barh([name.replace("_", " ") for name in labels], sharpes)
    ax.set_title("Base scenario: realized net Sharpe ratios")
    ax.set_xlabel("annualized arithmetic Sharpe, risk-free rate = 0")
    ax.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output / "base-sharpe.png", dpi=180)
    plt.close(fig)


def _report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# RiskLab experiment report",
        "",
        "> Controlled synthetic evidence. These are not historical returns and not investment advice.",
        "",
        "## Design",
        "",
        f"- Seed: `{payload['config']['seed']}`",
        f"- Simulated observations: `{payload['config']['n_days']}` days × `{payload['config']['n_assets']}` assets",
        f"- Heavy-tailed regimes: {', '.join(r['name'] for r in payload['market']['regimes'])}",
        f"- Bootstrap resamples per method/scenario comparison: `{payload['config']['bootstrap_resamples']}`",
        f"- Circular moving-block length: `{payload['config']['block_length']}` observations",
        "- Initial portfolio formation costs are excluded; subsequent one-way turnover is charged.",
        "",
        "## Covariance diagnostic at the first base-scenario rebalance",
        "",
        "| Diagnostic | Value |",
        "|---|---:|",
    ]
    for key, value in payload["covariance_diagnostics"].items():
        lines.append(f"| {key.replace('_', ' ')} | {value:.6g} |")
    lines.extend(["", "## Scenario results", ""])
    for scenario in payload["scenarios"]:
        lines.extend([
            f"### {scenario['scenario']['name']}",
            "",
            f"Window `{scenario['scenario']['window']}`, rebalance every `{scenario['scenario']['rebalance_every']}` days, cost `{scenario['scenario']['transaction_cost_bps']}` bps per unit of one-way turnover.",
            "",
            "| Method | Ann. return | Ann. vol | Sharpe | Max DD | Turnover | Failures | 95% annualized mean-return diff vs EW |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for method, entry in scenario["methods"].items():
            m = entry["metrics"]
            b = entry["bootstrap_vs_equal_weight"]
            interval = "baseline" if b is None else f"[{b['lower_95']:.2%}, {b['upper_95']:.2%}]"
            lines.append(
                f"| {method.replace('_', ' ')} | {m['annualized_return']:.2%} | {m['annualized_volatility']:.2%} | "
                f"{m['sharpe']:.3f} | {m['max_drawdown']:.2%} | {m['total_one_way_turnover']:.2f} | "
                f"{entry['optimizer_failures']} | {interval} |"
            )
        lines.append("")
    lines.extend([
        "## Interpretation boundary",
        "",
        "This experiment can reveal comparative behavior under a known synthetic stress process. It cannot establish that a method will outperform on future market data. Bootstrap intervals quantify resampling uncertainty conditional on this generated path; they do not include model risk from choosing the simulator itself.",
        "",
        "## Retained artifacts",
        "",
        "- `results.json`: complete configuration, environment, metrics, diagnostics, and uncertainty.",
        "- `summary.csv`: flat review table.",
        "- `base-cumulative-wealth.png`, `base-drawdowns.png`, `base-sharpe.png`: generated figures.",
    ])
    return "\n".join(lines) + "\n"


def run_experiment(
    output_dir: str | Path,
    *,
    config: ExperimentConfig | None = None,
    scenarios: tuple[Scenario, ...] | None = None,
) -> dict[str, Any]:
    config = config or ExperimentConfig()
    config.validate()
    scenarios = scenarios or default_scenarios(config.n_days)
    for scenario in scenarios:
        scenario.validate(config.n_days)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    market = simulate_market(config.n_days, config.n_assets, config.seed)
    scenario_payloads: list[dict[str, Any]] = []
    base_result: BacktestResult | None = None
    for index, scenario in enumerate(scenarios):
        payload, result = _scenario_result(market, config, scenario, index)
        scenario_payloads.append(payload)
        if scenario.name == "base" or base_result is None:
            base_result = result

    assert base_result is not None
    payload: dict[str, Any] = {
        "schema_version": "risklab.results.v1",
        "project_version": "0.1.0",
        "config": config.to_dict(),
        "market": {
            "returns_sha256": _sha256_array(market.returns),
            "asset_names": list(market.asset_names),
            "regimes": [asdict(record) for record in market.regimes],
            "synthetic": True,
        },
        "covariance_diagnostics": _covariance_diagnostics(market, scenarios[0].window),
        "scenarios": scenario_payloads,
        "environment": _runtime_environment(),
        "runtime_seconds": time.perf_counter() - started,
        "claim_boundary": {
            "supports": "comparative algorithm behavior under the retained deterministic synthetic process",
            "does_not_support": "historical or future investment performance, production execution, or suitability",
        },
    }
    (output / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_csv(output / "summary.csv", scenario_payloads)
    _plot_base(output, market, base_result, config.annualization)
    (output / "report.md").write_text(_report_markdown(payload), encoding="utf-8")
    return payload
