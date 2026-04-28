from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_business_actions(out_dir: Path, forecast_metrics: pd.DataFrame, rec_df: pd.DataFrame, tms_case: pd.DataFrame) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    wape = float(forecast_metrics.iloc[0]["WAPE"]) if not forecast_metrics.empty and "WAPE" in forecast_metrics.columns else np.nan
    sla_risk = float(tms_case["late_delivery_risk_score"].mean()) if not tms_case.empty and "late_delivery_risk_score" in tms_case.columns else np.nan
    locker_sites = int(rec_df["region_name"].nunique()) if not rec_df.empty and "region_name" in rec_df.columns else 0

    rows = [
        {
            "action_id": "A001", "priority": "High", "area": "Forecasting / WMS",
            "business_finding": "피크 시즌 수요 변동이 높음", "recommended_action": "피크 전 안전재고/피킹 인력 증설",
            "expected_impact": "stockout/출고지연 감소", "evidence_metric": "best_wape", "evidence_value": wape,
            "risk_level": "High", "owner_function": "WMS / Inventory", "dashboard_section": "Executive Impact Summary",
        },
        {
            "action_id": "A002", "priority": "Medium", "area": "TMS",
            "business_finding": "일부 지역 SLA 지연 리스크", "recommended_action": "고위험 지역 우선 배차/차량 증설",
            "expected_impact": "정시배송률 개선", "evidence_metric": "mean_late_delivery_risk_score", "evidence_value": sla_risk,
            "risk_level": "Medium", "owner_function": "TMS", "dashboard_section": "TMS Dashboard",
        },
        {
            "action_id": "A003", "priority": "Medium", "area": "Recommendation",
            "business_finding": "수요밀집 지역의 라스트마일 개선 여지", "recommended_action": "락커 후보지 우선 설치 검토",
            "expected_impact": "배송재시도/거리 감소", "evidence_metric": "recommended_locker_sites", "evidence_value": locker_sites,
            "risk_level": "Low", "owner_function": "Network Planning", "dashboard_section": "Recommendation",
        },
    ]
    path = out_dir / "business_action_recommendations.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def build_action_priority_matrix(actions_df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = actions_df.copy()
    impact_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
    risk_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
    df["expected_impact_score"] = df["priority"].map(impact_map).fillna(0.5)
    df["implementation_urgency"] = df["risk_level"].map(risk_map).fillna(0.5)
    path = out_dir / "action_priority_matrix.csv"
    df[["action_id", "priority", "area", "expected_impact_score", "implementation_urgency", "recommended_action"]].to_csv(path, index=False, encoding="utf-8-sig")
    return path


def generate_executive_summary(actions_df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    top = actions_df.head(5)
    lines = ["# Executive Summary", "", "공개데이터 + simulation layer 기반 의사결정 권고안입니다.", ""]
    for _, r in top.iterrows():
        lines.append(f"- [{r['priority']}] {r['business_finding']} -> {r['recommended_action']}")
    path = out_dir / "executive_summary.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
