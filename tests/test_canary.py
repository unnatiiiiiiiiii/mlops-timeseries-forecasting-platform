import json
from pathlib import Path

from mlops_forecasting.pipelines.canary_manager import evaluate_from_file


def test_canary_decision_promote(tmp_path):
    sample = {
        "stable": {"mape": 9.0, "p95_latency_ms": 180, "requests": 1000},
        "canary": {"mape": 9.2, "p95_latency_ms": 185, "requests": 300},
    }
    p = tmp_path / "metrics.json"
    p.write_text(json.dumps(sample))

    result = evaluate_from_file(str(p))
    assert result["decision"] in {"promote", "hold"}
