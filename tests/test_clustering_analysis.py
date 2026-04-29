from __future__ import annotations

from pathlib import Path
import pandas as pd

from parcelflow.advanced_analytics.clustering import run_clustering_analysis
from parcelflow.advanced_analytics.feature_builder import build_advanced_features


def test_clustering_outputs(tmp_path: Path) -> None:
    base = pd.DataFrame(
        {
            "date_key": pd.date_range("2025-01-01", periods=120, freq="D"),
            "dest_region_id": [1, 2, 3, 4] * 30,
            "category_id": [1, 2] * 60,
            "inbound_volume": [100 + (i % 15) for i in range(120)],
        }
    )
    feat = build_advanced_features(base)
    run_clustering_analysis(feat, tmp_path)
    q = pd.read_csv(tmp_path / "cluster_quality_scores.csv")
    assert "silhouette" in q.columns
