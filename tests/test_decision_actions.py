from __future__ import annotations

from pathlib import Path
import pandas as pd

from parcelflow.advanced_analytics.decision_actions import (
    build_action_priority_matrix,
    generate_business_actions,
    generate_executive_summary,
)


def test_decision_action_outputs(tmp_path: Path) -> None:
    fm = pd.DataFrame({"WAPE": [0.1]})
    rec = pd.DataFrame({"region_name": ["강남구", "송파구"]})
    tms = pd.DataFrame({"late_delivery_risk_score": [0.2, 0.3]})
    p = generate_business_actions(tmp_path, fm, rec, tms)
    df = pd.read_csv(p)
    assert "recommended_action" in df.columns
    mat = build_action_priority_matrix(df, tmp_path)
    assert mat.exists()
    md = generate_executive_summary(df, tmp_path)
    assert md.exists()
