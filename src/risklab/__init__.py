"""RiskLab: controlled experiments in allocation robustness."""

from .config import ExperimentConfig, Scenario
from .experiment import run_experiment

__all__ = ["ExperimentConfig", "Scenario", "run_experiment"]
__version__ = "0.1.0"
