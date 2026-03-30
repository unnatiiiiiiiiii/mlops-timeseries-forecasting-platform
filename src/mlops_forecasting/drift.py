from dataclasses import dataclass
import numpy as np
from scipy.stats import ks_2samp


@dataclass
class DriftResult:
    score: float
    drift_detected: bool


def detect_drift(reference: np.ndarray, current: np.ndarray, threshold: float) -> DriftResult:
    stat, _ = ks_2samp(reference, current)
    return DriftResult(score=float(stat), drift_detected=bool(stat > threshold))
