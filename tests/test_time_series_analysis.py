from __future__ import annotations

from pathlib import Path
import pandas as pd

from parcelflow.advanced_analytics.feature_builder import build_advanced_features
from parcelflow.advanced_analytics.time_series import run_time_series_analysis


def test_time_series_outputs(tmp_path: Path) -> None:
    base = pd.DataFrame(
        {
            "date_key": pd.date_range("2025-01-01", periods=90, freq="D"),
            "dest_region_id": [1] * 45 + [2] * 45,
            "category_id": [1, 2] * 45,
            "inbound_volume": [100 + (i % 8) for i in range(90)],
        }
    )
    feat = build_advanced_features(base)
    run_time_series_analysis(feat, tmp_path)
    acf = pd.read_csv(tmp_path / "acf_pacf.csv")
    assert {"function_type", "lag", "correlation"}.issubset(acf.columns)
