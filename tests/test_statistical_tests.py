from __future__ import annotations

from pathlib import Path
import pandas as pd

from parcelflow.advanced_analytics.feature_builder import build_advanced_features
from parcelflow.advanced_analytics.statistical_tests import run_statistical_tests


def test_statistical_tests_output(tmp_path: Path) -> None:
    base = pd.DataFrame(
        {
            "date_key": pd.date_range("2025-01-01", periods=90, freq="D"),
            "dest_region_id": [1] * 45 + [2] * 45,
            "category_id": [1, 2] * 45,
            "inbound_volume": [80 + (i % 10) for i in range(90)],
        }
    )
    feat = build_advanced_features(base)
    run_statistical_tests(feat, tmp_path)
    t = pd.read_csv(tmp_path / "statistical_tests.csv")
    assert {"p_value", "reject_null", "interpretation"}.issubset(t.columns)
