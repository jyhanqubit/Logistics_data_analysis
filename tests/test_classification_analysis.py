from __future__ import annotations

from pathlib import Path
import pandas as pd

from parcelflow.advanced_analytics.classification import run_classification_analysis
from parcelflow.advanced_analytics.feature_builder import build_advanced_features


def test_classification_outputs(tmp_path: Path) -> None:
    base = pd.DataFrame(
        {
            "date_key": pd.date_range("2025-01-01", periods=120, freq="D"),
            "dest_region_id": [1] * 60 + [2] * 60,
            "category_id": [1, 2] * 60,
            "inbound_volume": [90 + (i % 13) * 2 for i in range(120)],
        }
    )
    feat = build_advanced_features(base)
    run_classification_analysis(feat, tmp_path)
    m = pd.read_csv(tmp_path / "classification_model_metrics.csv")
    assert {"precision", "recall", "f1"}.issubset(m.columns)
