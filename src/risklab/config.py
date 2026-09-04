from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    name: str
    window: int
    rebalance_every: int
    transaction_cost_bps: float

    def validate(self, n_days: int) -> None:
        if not self.name.strip():
            raise ValueError("scenario name must be non-empty")
        if self.window < 30:
            raise ValueError("window must be at least 30 observations")
        if self.window >= n_days:
            raise ValueError("window must be shorter than the simulated history")
        if self.rebalance_every <= 0:
            raise ValueError("rebalance_every must be positive")
        if self.transaction_cost_bps < 0:
            raise ValueError("transaction_cost_bps must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExperimentConfig:
    n_assets: int = 8
    n_days: int = 1800
    seed: int = 20260903
    annualization: int = 252
    cvar_alpha: float = 0.95
    max_weight: float = 0.35
    bootstrap_resamples: int = 500
    block_length: int = 21

    def validate(self) -> None:
        if self.n_assets < 3:
            raise ValueError("n_assets must be at least 3")
        if self.n_days < 240:
            raise ValueError("n_days must be at least 240")
        if self.annualization <= 1:
            raise ValueError("annualization must exceed 1")
        if not 0.5 < self.cvar_alpha < 1.0:
            raise ValueError("cvar_alpha must be between 0.5 and 1")
        if not 0 < self.max_weight <= 1:
            raise ValueError("max_weight must be in (0, 1]")
        if self.bootstrap_resamples <= 0:
            raise ValueError("bootstrap_resamples must be positive")
        if not 1 <= self.block_length <= self.n_days:
            raise ValueError("block_length must be within the history")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_scenarios(n_days: int) -> tuple[Scenario, ...]:
    window_long = min(252, max(90, n_days // 3))
    window_short = min(126, max(60, n_days // 5))
    scenarios = (
        Scenario("base", window_long, 21, 10.0),
        Scenario("short_window", window_short, 21, 10.0),
        Scenario("high_cost", window_long, 21, 25.0),
        Scenario("low_frequency", window_long, 63, 10.0),
    )
    for scenario in scenarios:
        scenario.validate(n_days)
    return scenarios
