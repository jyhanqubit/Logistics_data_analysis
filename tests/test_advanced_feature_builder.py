from __future__ import annotations

import pandas as pd

from parcelflow.advanced_analytics.feature_builder import build_advanced_features


def test_build_advanced_features_runs() -> None:
    df = pd.DataFrame(
        {
            "date_key": pd.date_range("2025-01-01", periods=40, freq="D"),
            "dest_region_id": [1] * 20 + [2] * 20,
            "category_id": [1, 2] * 20,
            "inbound_volume": [100 + (i % 7) for i in range(40)],
        }
    )
    out = build_advanced_features(df)
    assert "lag_7" in out.columns
    assert "rolling_mean_28" in out.columns
