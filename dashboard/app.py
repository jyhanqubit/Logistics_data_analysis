from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

st.set_page_config(page_title="ParcelFlow AI Deep Analytics Dashboard", layout="wide")
st.title("ParcelFlow AI — Deep Analytics Dashboard")
st.caption("Made by 한정연(Jaiden Han)")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def metric_card(col, label: str, value: str) -> None:
    col.metric(label, value)


insights_actions = read_csv(OUTPUTS / "insights" / "business_action_recommendations.csv")
priority = read_csv(OUTPUTS / "insights" / "action_priority_matrix.csv")
exec_md = (OUTPUTS / "insights" / "executive_summary.md").read_text(encoding="utf-8") if (OUTPUTS / "insights" / "executive_summary.md").exists() else "executive_summary.md가 없습니다."

cases = {
    "oms_flow": read_csv(OUTPUTS / "analysis_cases" / "01_oms_order_flow.csv"),
    "oms_peak": read_csv(OUTPUTS / "analysis_cases" / "02_oms_peak_order_risk.csv"),
    "wms_inv": read_csv(OUTPUTS / "analysis_cases" / "03_wms_inventory_risk.csv"),
    "wms_pick": read_csv(OUTPUTS / "analysis_cases" / "04_wms_picking_workload.csv"),
    "tms_sla": read_csv(OUTPUTS / "analysis_cases" / "05_tms_delivery_sla.csv"),
    "tms_route": read_csv(OUTPUTS / "analysis_cases" / "06_tms_route_optimization.csv"),
    "fc": read_csv(OUTPUTS / "analysis_cases" / "07_demand_forecasting_region_category.csv"),
    "locker": read_csv(OUTPUTS / "analysis_cases" / "08_locker_site_recommendation.csv"),
}

reg_metrics = read_csv(OUTPUTS / "advanced_analytics" / "regression" / "regression_model_metrics.csv")
reg_pred = read_csv(OUTPUTS / "advanced_analytics" / "regression" / "regression_predictions.csv")
reg_fi = read_csv(OUTPUTS / "advanced_analytics" / "regression" / "regression_feature_importance.csv")

cls_metrics = read_csv(OUTPUTS / "advanced_analytics" / "classification" / "classification_model_metrics.csv")
cls_conf = read_csv(OUTPUTS / "advanced_analytics" / "classification" / "confusion_matrix.csv")

stat_tests = read_csv(OUTPUTS / "advanced_analytics" / "statistics" / "statistical_tests.csv")
stat_effect = read_csv(OUTPUTS / "advanced_analytics" / "statistics" / "effect_sizes.csv")

acf = read_csv(OUTPUTS / "advanced_analytics" / "time_series" / "acf_pacf.csv")
decomp = read_csv(OUTPUTS / "advanced_analytics" / "time_series" / "decomposition.csv")

cluster_assign = read_csv(OUTPUTS / "advanced_analytics" / "clustering" / "cluster_assignments.csv")
cluster_quality = read_csv(OUTPUTS / "advanced_analytics" / "clustering" / "cluster_quality_scores.csv")

forecast_metrics = read_csv(OUTPUTS / "forecasting" / "model_metrics.csv")
reco = read_csv(OUTPUTS / "recommender" / "site_recommendations.csv")
opt_form = (OUTPUTS / "advanced_analytics" / "optimization" / "optimization_formulation.md").read_text(encoding="utf-8") if (OUTPUTS / "advanced_analytics" / "optimization" / "optimization_formulation.md").exists() else "수식 파일 없음"
qubo_matrix = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_matrix_extended.csv")
qubo_sol = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_solution_extended.csv")
qubo_eig = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_eigenvalues.csv")
rl_base = read_csv(OUTPUTS / "advanced_analytics" / "rl" / "rl_baseline_policy_results.csv")

ops_oms = read_csv(OUTPUTS / "ops_simulation" / "oms_kpi.csv")
ops_wms = read_csv(OUTPUTS / "ops_simulation" / "wms_kpi.csv")
ops_tms = read_csv(OUTPUTS / "ops_simulation" / "tms_kpi.csv")

st.info("본 대시보드는 공개 생활물류/택배 물동량 기반 분석이며 OMS/WMS/TMS 이벤트는 simulation layer입니다. QUBO는 classical 검증 기반 quantum-ready PoC입니다.")

labels = [
    "1. Executive Impact Summary",
    "2. Data & Column Dictionary",
    "3. OMS Dashboard",
    "4. WMS Dashboard",
    "5. TMS Dashboard",
    "6. Regression Analysis",
    "7. Classification Analysis",
    "8. Statistical Analysis",
    "9. Time Series Analysis",
    "10. Clustering Analysis",
    "11. Forecasting",
    "12. Recommendation",
    "13. Optimization Formulation",
    "14. QUBO / Quantum PoC",
    "15. RL Feasibility",
    "16. Casebook / Talking Points",
]

tabs = st.tabs(labels)

with tabs[0]:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    best_wape = forecast_metrics["wape"].min() if not forecast_metrics.empty and "wape" in forecast_metrics.columns else None
    peak_regions = cases["oms_peak"]["region_name"].nunique() if not cases["oms_peak"].empty else 0
    high_stock = int((cases["wms_inv"].get("stockout_risk_score", pd.Series(dtype=float)) > 0.3).sum()) if not cases["wms_inv"].empty else 0
    high_sla = int((cases["tms_sla"].get("late_delivery_risk_score", pd.Series(dtype=float)) > 0.2).sum()) if not cases["tms_sla"].empty else 0
    reco_sites = reco["region_name"].nunique() if not reco.empty and "region_name" in reco.columns else 0
    save = cases["tms_route"].get("distance_saving_rate", pd.Series(dtype=float)).mean() if not cases["tms_route"].empty else None
    metric_card(c1, "Forecasting Best WAPE", f"{best_wape:.2%}" if best_wape is not None else "N/A")
    metric_card(c2, "Peak Risk Regions", str(peak_regions))
    metric_card(c3, "High Stockout Risk", str(high_stock))
    metric_card(c4, "High SLA Risk", str(high_sla))
    metric_card(c5, "Recommended Locker Sites", str(reco_sites))
    metric_card(c6, "Route Distance Saving", f"{save:.2%}" if save is not None else "N/A")

    st.markdown("### Top 5 Recommended Actions")
    if insights_actions.empty:
        st.warning("business_action_recommendations.csv 없음")
    else:
        st.dataframe(insights_actions.head(5), use_container_width=True)

    st.markdown("### Action Priority Matrix")
    if priority.empty:
        st.warning("action_priority_matrix.csv 없음")
    else:
        st.dataframe(priority, use_container_width=True)
        if {"expected_impact_score", "implementation_urgency"}.issubset(priority.columns):
            st.scatter_chart(priority[["expected_impact_score", "implementation_urgency"]])

    st.markdown("### Executive Summary")
    st.markdown(exec_md)
    st.markdown("### 데이터 한계\n- 공개데이터 기반 분석 + simulation layer\n- 특정 기업 내부 원천데이터 아님\n- QUBO는 실제 양자 하드웨어 실행 결과 아님")

with tabs[1]:
    col_dict_path = ROOT / "docs" / "dashboard" / "dashboard_column_dictionary.md"
    st.markdown(col_dict_path.read_text(encoding="utf-8") if col_dict_path.exists() else "column dictionary 문서 없음")

with tabs[2]:
    st.subheader("OMS Dashboard")
    df = cases["oms_flow"]
    st.dataframe(df.head(20) if not df.empty else pd.DataFrame({"message": ["01_oms_order_flow.csv 없음"]}), use_container_width=True)
    if not df.empty and {"region_name", "avg_order_to_release_hours"}.issubset(df.columns):
        st.bar_chart(df.groupby("region_name")["avg_order_to_release_hours"].mean())
    if not df.empty and "delayed_release_rate" in df.columns:
        st.dataframe(df.sort_values("delayed_release_rate", ascending=False).head(10), use_container_width=True)

with tabs[3]:
    st.subheader("WMS Dashboard")
    df = cases["wms_inv"]
    st.dataframe(df.head(20) if not df.empty else pd.DataFrame({"message": ["03_wms_inventory_risk.csv 없음"]}), use_container_width=True)
    if not df.empty and "stockout_risk_score" in df.columns:
        st.bar_chart(df.sort_values("stockout_risk_score", ascending=False).head(10).set_index("product_category")["stockout_risk_score"])
    df2 = cases["wms_pick"]
    if not df2.empty and "warehouse_utilization" in df2.columns:
        st.bar_chart(df2.groupby("warehouse_id")["warehouse_utilization"].mean())

with tabs[4]:
    st.subheader("TMS Dashboard")
    df = cases["tms_sla"]
    st.dataframe(df.head(20) if not df.empty else pd.DataFrame({"message": ["05_tms_delivery_sla.csv 없음"]}), use_container_width=True)
    if not df.empty and "late_delivery_risk_score" in df.columns:
        st.bar_chart(df.sort_values("late_delivery_risk_score", ascending=False).head(10).set_index("region_name")["late_delivery_risk_score"])
    if not df.empty and "on_time_delivery_rate" in df.columns:
        st.line_chart(df["on_time_delivery_rate"].head(30))

with tabs[5]:
    st.subheader("Regression Analysis")
    st.dataframe(reg_metrics if not reg_metrics.empty else pd.DataFrame({"message": ["regression metrics 없음"]}), use_container_width=True)
    if not reg_metrics.empty and {"model", "WAPE"}.issubset(reg_metrics.columns):
        st.bar_chart(reg_metrics.set_index("model")[["WAPE", "R2"]])
    if not reg_pred.empty and {"y_true", "y_pred"}.issubset(reg_pred.columns):
        st.line_chart(reg_pred[["y_true", "y_pred"]].head(100))
    st.dataframe(reg_fi.head(20) if not reg_fi.empty else pd.DataFrame({"message": ["feature importance 없음"]}), use_container_width=True)

with tabs[6]:
    st.subheader("Classification Analysis")
    st.dataframe(cls_metrics if not cls_metrics.empty else pd.DataFrame({"message": ["classification metrics 없음"]}), use_container_width=True)
    if not cls_metrics.empty and {"task", "recall"}.issubset(cls_metrics.columns):
        st.bar_chart(cls_metrics.groupby("task")["recall"].mean())
    st.dataframe(cls_conf if not cls_conf.empty else pd.DataFrame({"message": ["confusion_matrix 없음"]}), use_container_width=True)

with tabs[7]:
    st.subheader("Statistical Analysis")
    st.markdown("p-value < 0.05이면 유의하다고 보되 effect size와 비즈니스 의미를 함께 해석합니다.")
    st.dataframe(stat_tests if not stat_tests.empty else pd.DataFrame({"message": ["statistical_tests 없음"]}), use_container_width=True)
    st.dataframe(stat_effect if not stat_effect.empty else pd.DataFrame({"message": ["effect_sizes 없음"]}), use_container_width=True)

with tabs[8]:
    st.subheader("Time Series Analysis")
    st.dataframe(decomp.head(40) if not decomp.empty else pd.DataFrame({"message": ["decomposition 없음"]}), use_container_width=True)
    if not decomp.empty and {"observed", "trend"}.issubset(decomp.columns):
        st.line_chart(decomp[["observed", "trend"]].head(120))
    st.dataframe(acf.head(30) if not acf.empty else pd.DataFrame({"message": ["acf_pacf 없음"]}), use_container_width=True)

with tabs[9]:
    st.subheader("Clustering Analysis")
    st.dataframe(cluster_quality if not cluster_quality.empty else pd.DataFrame({"message": ["cluster_quality_scores 없음"]}), use_container_width=True)
    if not cluster_assign.empty and {"lat", "lon"}.issubset(cluster_assign.columns):
        st.map(cluster_assign.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])
    st.dataframe(cluster_assign.head(30) if not cluster_assign.empty else pd.DataFrame({"message": ["cluster_assignments 없음"]}), use_container_width=True)

with tabs[10]:
    st.subheader("Forecasting")
    st.dataframe(forecast_metrics if not forecast_metrics.empty else pd.DataFrame({"message": ["forecasting metrics 없음"]}), use_container_width=True)
    st.dataframe(cases["fc"].head(20) if not cases["fc"].empty else pd.DataFrame({"message": ["07_case 없음"]}), use_container_width=True)

with tabs[11]:
    st.subheader("Recommendation")
    st.dataframe(reco.head(20) if not reco.empty else pd.DataFrame({"message": ["site_recommendations 없음"]}), use_container_width=True)
    st.dataframe(cases["locker"].head(20) if not cases["locker"].empty else pd.DataFrame({"message": ["08_case 없음"]}), use_container_width=True)

with tabs[12]:
    st.subheader("Optimization Formulation")
    st.markdown(opt_form)
    st.latex(r"\min \sum_{k \in K} \sum_{i \in V}\sum_{j \in V, j\neq i} d_{ij} x_{ijk}")
    st.latex(r"\min x^TQx")

with tabs[13]:
    st.subheader("QUBO / Quantum PoC")
    st.markdown("QUBO matrix가 n×n이고 bitstring 길이가 n이면 binary variable은 n개입니다. QAOA 매핑 가능성은 설명 가능하지만 실제 양자 실험 수행으로 표현하지 않습니다.")
    st.dataframe(qubo_matrix.head(30) if not qubo_matrix.empty else pd.DataFrame({"message": ["qubo matrix 없음"]}), use_container_width=True)
    st.dataframe(qubo_sol.head(10) if not qubo_sol.empty else pd.DataFrame({"message": ["qubo solution 없음"]}), use_container_width=True)
    st.dataframe(qubo_eig.head(20) if not qubo_eig.empty else pd.DataFrame({"message": ["qubo eigenvalues 없음"]}), use_container_width=True)
    if not qubo_eig.empty and "eigenvalue" in qubo_eig.columns:
        st.bar_chart(qubo_eig.set_index("eigenvalue_index")["eigenvalue"])

with tabs[14]:
    st.subheader("RL Feasibility")
    st.dataframe(
        pd.DataFrame(
            [
                {"Method": "PPO", "Directly applicable?": "Yes", "Best use": "CVRP route policy learning", "Priority": "Medium/Future"},
                {"Method": "DPO", "Directly applicable?": "Not directly", "Best use": "Route explanation/ranking", "Priority": "Low/Optional"},
                {"Method": "QAOA", "Directly applicable?": "Yes", "Best use": "QUBO candidate selection", "Priority": "Medium"},
                {"Method": "OR-Tools", "Directly applicable?": "Yes", "Best use": "CVRP baseline", "Priority": "High"},
            ]
        ),
        use_container_width=True,
    )
    st.dataframe(rl_base if not rl_base.empty else pd.DataFrame({"message": ["rl_baseline_policy_results 없음"]}), use_container_width=True)

with tabs[15]:
    st.subheader("Casebook / Talking Points")
    cp = ROOT / "docs" / "dashboard" / "dashboard_casebook_talking_points.md"
    st.markdown(cp.read_text(encoding="utf-8") if cp.exists() else "talking points 문서 없음")
    st.dataframe(insights_actions if not insights_actions.empty else pd.DataFrame({"message": ["action recommendations 없음"]}), use_container_width=True)
