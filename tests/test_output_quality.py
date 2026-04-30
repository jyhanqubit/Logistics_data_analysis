from __future__ import annotations

from pathlib import Path

import pandas as pd


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def test_business_actions_quality():
    df = _read(Path("outputs/insights/business_action_recommendations.csv"))
    if df.empty:
        return
    assert df["recommended_action"].notna().all()
    bad_tokens = {"Action", "사유 정보 없음"}
    assert not df["recommended_action"].astype(str).isin(bad_tokens).any()
    assert len(df) >= 8


def test_cluster_assignment_quality():
    df = _read(Path("outputs/advanced_analytics/clustering/cluster_assignments.csv"))
    if df.empty:
        return
    assert not df["region_name"].astype(str).str.startswith("Region-").any()
    assert df["lat"].nunique() > 1 and df["lon"].nunique() > 1


def test_wms_and_tms_quality():
    wms = _read(Path("outputs/analysis_cases/03_wms_inventory_risk.csv"))
    if not wms.empty and "stockout_risk_score" in wms.columns:
        assert not (wms["stockout_risk_score"].fillna(0) == 0).all()

    tms = _read(Path("outputs/analysis_cases/05_tms_delivery_sla.csv"))
    if not tms.empty and "region_name" in tms.columns:
        assert tms["region_name"].nunique() >= 5


def test_qubo_bitstring_consistency():
    path = Path("outputs/advanced_analytics/qubo/qubo_solution_extended.csv")
    sol = pd.read_csv(path, dtype={"bitstring": str}) if path.exists() else pd.DataFrame()
    mat = _read(Path("outputs/advanced_analytics/qubo/qubo_matrix_extended.csv"))
    if sol.empty or mat.empty or "bitstring" not in sol.columns:
        return
    matrix_size = len(mat)
    lengths = sol["bitstring"].astype(str).str.len()
    assert (lengths == matrix_size).all()
