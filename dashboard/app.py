from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs" / "dashboard"

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


def read_md(path: Path, fallback: str) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else fallback


insights_actions = read_csv(OUTPUTS / "insights" / "business_action_recommendations.csv")
priority = read_csv(OUTPUTS / "insights" / "action_priority_matrix.csv")
exec_md = read_md(OUTPUTS / "insights" / "executive_summary.md", "executive_summary.md가 없습니다.")
score_md = read_md(DOCS / "action_scoring_method.md", "action scoring 설명 문서가 없습니다.")
data_spec_md = read_md(DOCS / "dashboard_data_spec.md", "data spec 문서가 없습니다.")

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
cls_fi = read_csv(OUTPUTS / "advanced_analytics" / "classification" / "classification_feature_importance.csv")

stat_tests = read_csv(OUTPUTS / "advanced_analytics" / "statistics" / "statistical_tests.csv")
stat_effect = read_csv(OUTPUTS / "advanced_analytics" / "statistics" / "effect_sizes.csv")
stat_group = read_csv(OUTPUTS / "advanced_analytics" / "statistics" / "group_summary.csv")

acf = read_csv(OUTPUTS / "advanced_analytics" / "time_series" / "acf_pacf.csv")
decomp = read_csv(OUTPUTS / "advanced_analytics" / "time_series" / "decomposition.csv")
ccf = read_csv(OUTPUTS / "advanced_analytics" / "time_series" / "cross_correlation.csv")

cluster_assign = read_csv(OUTPUTS / "advanced_analytics" / "clustering" / "cluster_assignments.csv")
cluster_quality = read_csv(OUTPUTS / "advanced_analytics" / "clustering" / "cluster_quality_scores.csv")

forecast_metrics = read_csv(OUTPUTS / "forecasting" / "model_metrics.csv")
forecast_pred = read_csv(OUTPUTS / "forecasting" / "forecast_predictions.csv")
reco = read_csv(OUTPUTS / "recommender" / "site_recommendations.csv")
opt_form = read_md(OUTPUTS / "advanced_analytics" / "optimization" / "optimization_formulation.md", "수식 파일 없음")
route_plan = read_csv(OUTPUTS / "optimization" / "route_plan.csv")
qubo_matrix = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_matrix_extended.csv")
qubo_sol = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_solution_extended.csv")
qubo_eig = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_eigenvalues.csv")
qubo_cand = read_csv(OUTPUTS / "advanced_analytics" / "qubo" / "qubo_candidates.csv")

st.info("실제 데이터는 공개 생활물류/택배 물동량 데이터이며 OMS/WMS/TMS 이벤트는 simulation layer입니다. QUBO는 quantum-ready formulation의 classical 검증 결과입니다.")

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
]

tabs = st.tabs(labels)

with tabs[0]:
    st.markdown("### Executive Actions")
    if insights_actions.empty:
        st.warning("actions 데이터가 없습니다.")
    else:
        preview = insights_actions.head(8).copy()
        for _, row in preview.iterrows():
            title = row.get("action_title", row.get("business_action", "Action"))
            reason = row.get("reason", row.get("action_reason", "사유 정보 없음"))
            st.markdown(f"#### ✅ {title}")
            st.write(reason)
    st.markdown("### 데이터 한계\n- 공개데이터 + simulation layer\n- 특정 기업 내부 원천데이터 아님\n- QUBO는 실제 양자 하드웨어 실행 결과 아님")

with tabs[1]:
    st.markdown("### 데이터 명세")
    st.markdown(data_spec_md)

with tabs[2]:
    st.subheader("OMS Dashboard")
    df = cases["oms_flow"]
    st.dataframe(df.head(20) if not df.empty else pd.DataFrame({"message": ["01_oms_order_flow.csv 없음"]}), use_container_width=True)
    if not df.empty and {"region_name", "order_count"}.issubset(df.columns):
        st.bar_chart(df.groupby("region_name")["order_count"].sum())
    if not df.empty and {"product_category", "order_count"}.issubset(df.columns):
        st.bar_chart(df.groupby("product_category")["order_count"].sum())

with tabs[3]:
    st.subheader("WMS Dashboard")
    inv = cases["wms_inv"]
    pick = cases["wms_pick"]
    st.dataframe(inv.head(20) if not inv.empty else pd.DataFrame({"message": ["03_wms_inventory_risk.csv 없음"]}), use_container_width=True)
    if not inv.empty and "stockout_risk_score" in inv.columns:
        chart_df = inv.sort_values("stockout_risk_score", ascending=False).head(15)
        st.altair_chart(
            alt.Chart(chart_df).mark_bar().encode(
                x=alt.X("stockout_risk_score:Q", title="Stockout risk score"),
                y=alt.Y("product_category:N", sort="-x", title="Product category"),
                color=alt.Color("reorder_priority:N", title="Priority"),
                tooltip=list(chart_df.columns),
            ).properties(title="WMS Stockout Risk by Category"),
            use_container_width=True,
        )
    if not pick.empty and "warehouse_utilization" in pick.columns:
        util = pick.groupby("warehouse_name", as_index=False)["warehouse_utilization"].mean()
        st.altair_chart(
            alt.Chart(util).mark_bar().encode(
                x=alt.X("warehouse_utilization:Q", title="Avg warehouse utilization"),
                y=alt.Y("warehouse_name:N", sort="-x", title="Warehouse"),
                tooltip=["warehouse_name", "warehouse_utilization"],
            ).properties(title="WMS Warehouse Utilization"),
            use_container_width=True,
        )

with tabs[4]:
    st.subheader("TMS Dashboard")
    st.caption("TMS는 공개 물동량 기반 simulation 데이터입니다.")
    df = cases["tms_sla"]
    st.dataframe(df.head(20) if not df.empty else pd.DataFrame({"message": ["05_tms_delivery_sla.csv 없음"]}), use_container_width=True)
    if not df.empty and "late_delivery_risk_score" in df.columns:
        tdf = df.groupby("region_name", as_index=False)["late_delivery_risk_score"].mean().sort_values("late_delivery_risk_score", ascending=False).head(15)
        st.altair_chart(
            alt.Chart(tdf).mark_bar().encode(
                x=alt.X("late_delivery_risk_score:Q", title="Avg late delivery risk"),
                y=alt.Y("region_name:N", sort="-x", title="Region"),
                color=alt.value("#e15759"),
                tooltip=["region_name", "late_delivery_risk_score"],
            ).properties(title="TMS SLA Risk by Region"),
            use_container_width=True,
        )

with tabs[5]:
    st.subheader("Regression Analysis")
    st.markdown("**Input features**: time, lag, rolling, entropy, distance proxy 등 (`feature_builder`)\n\n**Target**: `inbound_volume`.")
    st.dataframe(reg_metrics if not reg_metrics.empty else pd.DataFrame({"message": ["regression metrics 없음"]}), use_container_width=True)
    if not reg_metrics.empty and {"model", "wape"}.issubset(reg_metrics.columns):
        st.altair_chart(alt.Chart(reg_metrics).mark_bar().encode(x=alt.X("wape:Q", title="WAPE"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "wape"]), use_container_width=True)
        if "r2" in reg_metrics.columns:
            st.altair_chart(alt.Chart(reg_metrics).mark_bar(color="#4e79a7").encode(x=alt.X("r2:Q", title="R²"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "r2"]), use_container_width=True)
    elif not reg_metrics.empty and {"model", "WAPE"}.issubset(reg_metrics.columns):
        st.bar_chart(reg_metrics.set_index("model")[["WAPE", "R2"]])
    if not reg_pred.empty and {"y_true", "y_pred"}.issubset(reg_pred.columns):
        st.line_chart(reg_pred[["y_true", "y_pred"]].head(120))
    st.dataframe(reg_fi.head(20) if not reg_fi.empty else pd.DataFrame({"message": ["feature importance 없음"]}), use_container_width=True)

with tabs[6]:
    st.subheader("Classification Analysis")
    st.markdown("**Input features**: feature_builder 산출 feature\n\n**Targets**: `peak_demand_risk`, `stockout_risk`, `late_delivery_risk`.")
    st.dataframe(cls_metrics if not cls_metrics.empty else pd.DataFrame({"message": ["classification metrics 없음"]}), use_container_width=True)
    if not cls_metrics.empty and {"task", "f1"}.issubset(cls_metrics.columns):
        f1_df = cls_metrics.groupby("model", as_index=False)["f1"].mean().sort_values("f1", ascending=False)
        st.altair_chart(alt.Chart(f1_df).mark_bar().encode(x=alt.X("f1:Q", title="F1 score"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "f1"]), use_container_width=True)
        best_model = f1_df.iloc[0]["model"] if not f1_df.empty else None
        if best_model and not cls_conf.empty and "model" in cls_conf.columns:
            st.markdown(f"**Best model confusion matrix: {best_model}**")
            st.dataframe(cls_conf[cls_conf["model"] == best_model], use_container_width=True)
    st.dataframe(cls_conf if not cls_conf.empty else pd.DataFrame({"message": ["confusion_matrix 없음"]}), use_container_width=True)
    st.dataframe(cls_fi.head(20) if not cls_fi.empty else pd.DataFrame({"message": ["classification feature importance 없음"]}), use_container_width=True)

with tabs[7]:
    st.subheader("Statistical Analysis")
    st.markdown("p-value < 0.05이면 유의하다고 보되 effect size와 비즈니스 의미를 함께 해석합니다.")
    st.dataframe(stat_tests if not stat_tests.empty else pd.DataFrame({"message": ["statistical_tests 없음"]}), use_container_width=True)
    st.dataframe(stat_effect if not stat_effect.empty else pd.DataFrame({"message": ["effect_sizes 없음"]}), use_container_width=True)
    if not stat_group.empty:
        st.dataframe(stat_group, use_container_width=True)

with tabs[8]:
    st.subheader("Time Series Analysis")
    st.caption("가능한 데이터 범위(예: 2018~2023 공개데이터 또는 현재 로드된 데이터)로 분석합니다.")
    st.dataframe(decomp.head(40) if not decomp.empty else pd.DataFrame({"message": ["decomposition 없음"]}), use_container_width=True)
    if not decomp.empty and {"observed", "trend", "seasonal", "arima_fitted"}.issubset(decomp.columns):
        st.line_chart(decomp[["observed", "trend", "seasonal", "arima_fitted"]].head(180))
    st.dataframe(acf.head(40) if not acf.empty else pd.DataFrame({"message": ["acf_pacf 없음"]}), use_container_width=True)
    if not acf.empty and {"lag", "correlation", "function_type"}.issubset(acf.columns):
        acf_df = acf[acf["function_type"] == "ACF"].head(28)
        pacf_df = acf[acf["function_type"] == "PACF"].head(28)
        st.altair_chart(alt.Chart(acf_df).mark_line(point=True).encode(x=alt.X("lag:Q", title="Lag"), y=alt.Y("correlation:Q", title="ACF"), tooltip=["lag", "correlation"]), use_container_width=True)
        st.altair_chart(alt.Chart(pacf_df).mark_line(point=True).encode(x=alt.X("lag:Q", title="Lag"), y=alt.Y("correlation:Q", title="PACF"), tooltip=["lag", "correlation"]), use_container_width=True)
    st.dataframe(ccf.head(20) if not ccf.empty else pd.DataFrame({"message": ["cross_correlation 없음"]}), use_container_width=True)

with tabs[9]:
    st.subheader("Clustering Analysis")
    st.markdown("**Input features**: avg_volume, cv, peak_ratio, growth_rate, category_entropy, locker_score")
    st.dataframe(cluster_quality if not cluster_quality.empty else pd.DataFrame({"message": ["cluster_quality_scores 없음"]}), use_container_width=True)
    if not cluster_assign.empty and {"lat", "lon", "cluster_id"}.issubset(cluster_assign.columns):
        try:
            import pydeck as pdk

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=cluster_assign,
                get_position="[lon, lat]",
                get_fill_color="[cluster_id*45 % 255, 120, 255 - cluster_id*35 % 255, 180]",
                get_radius=120,
                pickable=True,
            )
            view_state = pdk.ViewState(latitude=float(cluster_assign["lat"].mean()), longitude=float(cluster_assign["lon"].mean()), zoom=10)
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{region_name} | {cluster_label}"}))
        except Exception:
            st.map(cluster_assign.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])
    st.dataframe(cluster_assign.head(30) if not cluster_assign.empty else pd.DataFrame({"message": ["cluster_assignments 없음"]}), use_container_width=True)

with tabs[10]:
    st.subheader("Forecasting")
    st.markdown("예측 대상: `region × category × date` 단위 `inbound_volume`.")
    st.dataframe(forecast_metrics if not forecast_metrics.empty else pd.DataFrame({"message": ["forecasting metrics 없음"]}), use_container_width=True)
    if not forecast_pred.empty and {"date_key", "inbound_volume", "prediction"}.issubset(forecast_pred.columns):
        fp = forecast_pred.copy()
        fp["date_key"] = pd.to_datetime(fp["date_key"], errors="coerce")
        fp = fp[fp["date_key"].dt.year == 2023]
        if not fp.empty:
            ts = fp.groupby("date_key", as_index=False)[["inbound_volume", "prediction"]].sum()
            melted = ts.melt(id_vars="date_key", var_name="series", value_name="volume")
            st.altair_chart(alt.Chart(melted).mark_line().encode(x=alt.X("date_key:T", title="Date"), y=alt.Y("volume:Q", title="Volume"), color=alt.Color("series:N", title="Series")), use_container_width=True)
    st.dataframe(cases["fc"].head(20) if not cases["fc"].empty else pd.DataFrame({"message": ["07_case 없음"]}), use_container_width=True)

with tabs[11]:
    st.subheader("Recommendation")
    st.markdown("이커머스 지수는 본 PoC의 지역 특성 proxy feature(합성/외생 지표)로 사용됩니다.")
    st.dataframe(cases["locker"].head(20) if not cases["locker"].empty else pd.DataFrame({"message": ["08_case 없음"]}), use_container_width=True)

with tabs[12]:
    st.subheader("Optimization Formulation")
    st.markdown(opt_form)
    st.markdown("- $d_{ij}$: 노드 i→j 거리\n- $x_{ijk}$: 차량 k가 i→j 이동하면 1\n- 예시: `route_plan.csv`의 vehicle별 stop 이동이 $x_{ijk}$에 대응")
    st.latex(r"\min \sum_{k \in K} \sum_{i \in V}\sum_{j \in V, j\neq i} d_{ij} x_{ijk}")
    st.latex(r"\min x^TQx")
    if not route_plan.empty:
        st.markdown("### Suggested Route Order (from route_plan)")
        st.dataframe(route_plan.sort_values(["vehicle_id"]).head(100), use_container_width=True)

with tabs[13]:
    st.subheader("QUBO / Quantum PoC")
    st.markdown(
        "- bitstring 각 자리: 후보지 선택(1)/미선택(0)\n"
        "- 길이 n bitstring ↔ n개 binary variable\n"
        "- eigenvalue는 Q 행렬 스펙트럼 이해용이며, 최적 bitstring을 직접 주지 않음\n"
        "- 실제 최적해는 binary 해를 평가해 도출"
    )
    st.dataframe(qubo_cand.head(20) if not qubo_cand.empty else pd.DataFrame({"message": ["qubo candidates 없음"]}), use_container_width=True)
    st.dataframe(qubo_matrix.head(30) if not qubo_matrix.empty else pd.DataFrame({"message": ["qubo matrix 없음"]}), use_container_width=True)
    st.dataframe(qubo_sol.head(10) if not qubo_sol.empty else pd.DataFrame({"message": ["qubo solution 없음"]}), use_container_width=True)
    st.dataframe(qubo_eig.head(20) if not qubo_eig.empty else pd.DataFrame({"message": ["qubo eigenvalues 없음"]}), use_container_width=True)
    if not qubo_eig.empty and "eigenvalue" in qubo_eig.columns:
        st.altair_chart(
            alt.Chart(qubo_eig).mark_line(point=True).encode(
                x=alt.X("eigenvalue_index:Q", title="Eigenvalue index"),
                y=alt.Y("eigenvalue:Q", title="Eigenvalue"),
                tooltip=["eigenvalue_index", "eigenvalue"],
            ).properties(title="QUBO Eigenvalue Spectrum"),
            use_container_width=True,
        )
    if not qubo_sol.empty:
        st.markdown("### Top QUBO state meaning")
        top = qubo_sol.sort_values("energy").head(1)
        if not top.empty:
            st.write(f"bitstring={top.iloc[0].get('bitstring')} / selected_count={top.iloc[0].get('selected_count')} / energy={top.iloc[0].get('energy')}")
