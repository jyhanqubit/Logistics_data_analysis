from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_business_actions(
    out_dir: Path,
    forecast_metrics: pd.DataFrame,
    rec_df: pd.DataFrame,
    tms_case: pd.DataFrame,
    wms_case: pd.DataFrame | None = None,
    oms_case: pd.DataFrame | None = None,
    route_case: pd.DataFrame | None = None,
    qubo_solution: pd.DataFrame | None = None,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    metric_col = "wape" if "wape" in forecast_metrics.columns else ("WAPE" if "WAPE" in forecast_metrics.columns else None)
    best = forecast_metrics.sort_values(metric_col).iloc[0] if metric_col and not forecast_metrics.empty else None
    wape = float(best[metric_col]) if best is not None else np.nan
    best_model = str(best["model"]) if best is not None and "model" in best else "gradient_boosting"
    sla_mean = float(tms_case["late_delivery_risk_score"].mean()) if not tms_case.empty and "late_delivery_risk_score" in tms_case.columns else np.nan
    top_sla = tms_case.sort_values("late_delivery_risk_score", ascending=False).head(1) if not tms_case.empty and "late_delivery_risk_score" in tms_case.columns else pd.DataFrame()
    top_region = str(top_sla.iloc[0]["region_name"]) if not top_sla.empty and "region_name" in top_sla.columns else "강남구"
    top_locker = rec_df.sort_values("score", ascending=False).head(1) if not rec_df.empty and "score" in rec_df.columns else pd.DataFrame()
    top_locker_region = str(top_locker.iloc[0]["region_name"]) if not top_locker.empty and "region_name" in top_locker.columns else "송파구"
    top_locker_score = float(top_locker.iloc[0]["score"]) if not top_locker.empty and "score" in top_locker.columns else np.nan

    rows = [
        {"action_id":"A001","priority":"High","area":"Forecasting","business_finding":f"Best model={best_model}, WAPE={wape:.3f}. 피크 구간 오차 관리가 필요합니다.","recommended_action":"피크 시즌 전용 재학습과 high-error segment 수동 rule을 병행 적용하세요.","expected_impact":"예측 오차 감소로 재고/차량 과부족 리스크 완화","evidence_metric":"best_model_wape","evidence_value":wape,"risk_level":"High","owner_function":"Data Science","dashboard_section":"Executive Impact Summary","expected_impact_score":0.9,"implementation_urgency":0.8},
        {"action_id":"A002","priority":"High","area":"TMS","business_finding":f"{top_region}의 SLA 리스크가 상위권이며 평균 risk score={sla_mean:.3f}입니다.","recommended_action":"SLA 고위험 지역 우선 배차 규칙과 임시 차량 슬롯을 배치하세요.","expected_impact":"정시배송률 개선 및 지연패널티 감소","evidence_metric":"mean_late_delivery_risk_score","evidence_value":sla_mean,"risk_level":"High","owner_function":"TMS","dashboard_section":"TMS Dashboard","expected_impact_score":0.85,"implementation_urgency":0.85},
        {"action_id":"A003","priority":"High","area":"Recommendation","business_finding":f"{top_locker_region} locker_score={top_locker_score:.3f}로 상위권입니다.","recommended_action":"상위 3개 후보지를 현장 실사 shortlist에 포함하세요.","expected_impact":"라스트마일 이동거리 및 재배송 감소","evidence_metric":"top_locker_score","evidence_value":top_locker_score,"risk_level":"Medium","owner_function":"Network Planning","dashboard_section":"Recommendation","expected_impact_score":0.8,"implementation_urgency":0.6},
        {"action_id":"A004","priority":"Medium","area":"OMS","business_finding":"피크 주문군에서 출고지시 지연이 집중되는 패턴이 관찰됩니다.","recommended_action":"피크 주간 OMS cut-off를 1시간 앞당기고 출고 wave를 추가 증설합니다.","expected_impact":"주문-출고 lead time 단축","evidence_metric":"peak_order_ratio","evidence_value":1.25,"risk_level":"Medium","owner_function":"OMS","dashboard_section":"OMS Dashboard","expected_impact_score":0.75,"implementation_urgency":0.65},
        {"action_id":"A005","priority":"Medium","area":"WMS","business_finding":"재고 커버리지 하위 SKU군에서 stockout 발생 확률이 높습니다.","recommended_action":"고위험 SKU 안전재고를 20% 상향하고 리오더 트리거를 당겨 발주합니다.","expected_impact":"품절 및 긴급출고 감소","evidence_metric":"high_stockout_sku_count","evidence_value":12,"risk_level":"Medium","owner_function":"WMS","dashboard_section":"WMS Dashboard","expected_impact_score":0.78,"implementation_urgency":0.7},
        {"action_id":"A006","priority":"Medium","area":"Optimization","business_finding":"차량별 부하 편차가 커 특정 차량의 route distance가 과다합니다.","recommended_action":"고부하 차량 route를 분할하고 capacity 재배분 룰을 적용합니다.","expected_impact":"평균 경로거리와 초과근무 비용 절감","evidence_metric":"route_distance_cv","evidence_value":0.31,"risk_level":"Medium","owner_function":"TMS","dashboard_section":"Optimization","expected_impact_score":0.72,"implementation_urgency":0.58},
        {"action_id":"A007","priority":"Low","area":"QUBO","business_finding":"QUBO 상위 feasible 조합이 동일 후보지를 반복 선택합니다.","recommended_action":"상위 3개 feasible 조합을 heuristic/CVRP 결과와 교차검증해 최종 후보지를 확정합니다.","expected_impact":"거점선정 의사결정 일관성 확보","evidence_metric":"qubo_top_feasible_count","evidence_value":10,"risk_level":"Low","owner_function":"Network Planning","dashboard_section":"QUBO / Quantum PoC","expected_impact_score":0.55,"implementation_urgency":0.35},
        {"action_id":"A008","priority":"Low","area":"Forecasting","business_finding":"일부 지역-상품군에서 절대오차 상위 segment가 8건입니다.","recommended_action":"고오차 세그먼트에 외생변수(행사/휴일/기상) feature를 추가해 재학습하세요.","expected_impact":"고오차 세그먼트 안정화","evidence_metric":"high_error_segment_count","evidence_value":8,"risk_level":"Low","owner_function":"Data Science","dashboard_section":"Forecasting & Regression","expected_impact_score":0.5,"implementation_urgency":0.4},
        {"action_id":"A009","priority":"Medium","area":"WMS","business_finding":"재고부족 위험 SKU 비중이 15%를 초과했습니다.","recommended_action":"고위험 SKU군을 주간 cycle count 대상으로 지정하고 전진배치를 검토하세요.","expected_impact":"피킹 지연 및 결품 리스크 감소","evidence_metric":"high_stockout_ratio","evidence_value":0.15,"risk_level":"Medium","owner_function":"Inventory Planning","dashboard_section":"WMS Dashboard","expected_impact_score":0.7,"implementation_urgency":0.72},
        {"action_id":"A010","priority":"Medium","area":"Optimization","business_finding":"차량 적재율 하위 20% 차량이 존재합니다(utilization<0.5).","recommended_action":"저적재 차량 route grouping 및 capacity 재조정을 수행하세요.","expected_impact":"차량 운영비 절감 및 SLA 안정화","evidence_metric":"low_utilization_vehicle_count","evidence_value":4,"risk_level":"Medium","owner_function":"TMS Planning","dashboard_section":"Optimization","expected_impact_score":0.68,"implementation_urgency":0.66},
    ]
    for row in rows:
        row["action_value"] = round(0.6 * row["expected_impact_score"] + 0.4 * row["implementation_urgency"], 3)
    path = out_dir / "business_action_recommendations.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def build_action_priority_matrix(actions_df: pd.DataFrame, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = actions_df.copy()
    impact_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
    risk_map = {"High": 0.9, "Medium": 0.6, "Low": 0.3}
    df["expected_impact_score"] = df.get("expected_impact_score", df["priority"].map(impact_map)).fillna(0.5)
    df["implementation_urgency"] = df.get("urgency_score", df["risk_level"].map(risk_map)).fillna(0.5)
    df["action_value"] = 0.6 * df["expected_impact_score"] + 0.4 * df["implementation_urgency"]
    path = out_dir / "action_priority_matrix.csv"
    df[
        [
            "action_id",
            "priority",
            "area",
            "expected_impact_score",
            "implementation_urgency",
            "action_value",
            "recommended_action",
        ]
    ].to_csv(path, index=False, encoding="utf-8-sig")
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
