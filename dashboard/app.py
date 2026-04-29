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
    "2. OMS Dashboard",
    "3. WMS Dashboard",
    "4. TMS Dashboard",
    "5. Forecasting & Regression",
    "6. Classification Risk Models",
    "7. Statistical Tests",
    "8. Time Series Analysis",
    "9. Clustering & Map",
    "10. Recommendation",
    "11. Optimization",
    "12. QUBO / Quantum PoC",
    "13. Data Dictionary",
]

tabs = st.tabs(labels)

with tabs[0]:
    st.markdown("### Main Message")
    if not insights_actions.empty:
        top_area = insights_actions["area"].astype(str).value_counts().index[0]
        top_act = insights_actions.head(1).iloc[0]
        msg = (
            f"공개 생활물류 데이터와 simulation layer 분석 결과, **{top_area}** 영역 리스크가 가장 높게 나타났습니다. "
            f"특히 `{top_act.get('business_finding', '핵심 지표')}`에 따라 `{top_act.get('recommended_action', '우선 액션')}`를 단기 우선순위로 실행해야 합니다. "
            "중기적으로는 추천 후보지/최적화 결과를 결합해 라스트마일 부하를 완화하는 것이 타당합니다."
        )
    else:
        msg = "핵심 액션 데이터가 부족합니다. pipeline 실행 후 insights 산출물을 확인하세요."
    st.info(msg)

    c1, c2, c3, c4 = st.columns(4)
    high_actions = int((insights_actions["priority"] == "High").sum()) if not insights_actions.empty and "priority" in insights_actions.columns else 0
    top_risk_area = insights_actions["area"].value_counts().index[0] if not insights_actions.empty and "area" in insights_actions.columns else "N/A"
    best_model = forecast_metrics.sort_values("wape").head(1) if not forecast_metrics.empty and "wape" in forecast_metrics.columns else pd.DataFrame()
    best_model_name = best_model.iloc[0]["model"] if not best_model.empty else "N/A"
    best_wape = float(best_model.iloc[0]["wape"]) if not best_model.empty else float("nan")
    high_stock = int((cases["wms_inv"]["stockout_risk_score"] > 0.3).sum()) if not cases["wms_inv"].empty and "stockout_risk_score" in cases["wms_inv"].columns else 0
    c1.metric("High Priority Actions", high_actions)
    c2.metric("Top Risk Area", top_risk_area)
    c3.metric("Best Forecast / WAPE", f"{best_model_name} / {best_wape:.3f}" if best_model_name != "N/A" else "N/A")
    c4.metric("High Stockout Risk Count", high_stock)

    c5, c6, c7 = st.columns(3)
    high_sla = int((cases["tms_sla"]["late_delivery_risk_score"] > 0.2).sum()) if not cases["tms_sla"].empty and "late_delivery_risk_score" in cases["tms_sla"].columns else 0
    top_locker = reco.sort_values("score", ascending=False).head(1) if not reco.empty and "score" in reco.columns else pd.DataFrame()
    top_locker_name = top_locker.iloc[0]["region_name"] if not top_locker.empty else "N/A"
    qubo_n = len(qubo_cand) if not qubo_cand.empty else 0
    qubo_k = int(qubo_sol["selected_count"].mode().iloc[0]) if not qubo_sol.empty and "selected_count" in qubo_sol.columns else 0
    c5.metric("High SLA Risk Count", high_sla)
    c6.metric("Top Locker Candidate", str(top_locker_name))
    c7.metric("QUBO N / K", f"{qubo_n} / {qubo_k}")

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
    st.markdown("### Action Priority Matrix")
    if not priority.empty and {"expected_impact_score", "implementation_urgency"}.issubset(priority.columns):
        st.altair_chart(
            alt.Chart(priority).mark_circle(size=90).encode(
                x=alt.X("implementation_urgency:Q", title="Implementation Urgency"),
                y=alt.Y("expected_impact_score:Q", title="Expected Impact Score"),
                color=alt.Color("priority:N", title="Priority"),
                tooltip=["action_id", "area", "recommended_action"],
            ),
            use_container_width=True,
        )
    st.markdown("### Data Limitation\n본 대시보드는 공개 생활물류/택배 물동량 데이터를 기반으로 하며, OMS/WMS/TMS 이벤트는 simulation layer입니다. QUBO는 실제 양자 하드웨어 실행 결과가 아니라 classical 검증 결과입니다.")

with tabs[1]:
    st.subheader("OMS Dashboard")
    st.markdown("**Business Question**: 어떤 지역/상품군에서 주문-출고 병목이 발생하고 있는가?")
    df = cases["oms_flow"]
    if not df.empty and {"order_count", "avg_order_to_release_hours", "p95_order_to_release_hours", "delayed_release_rate"}.issubset(df.columns):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Orders", int(df["order_count"].sum()))
        c2.metric("Avg Release Hours", f"{df['avg_order_to_release_hours'].mean():.2f}")
        c3.metric("P95 Release Hours", f"{df['p95_order_to_release_hours'].mean():.2f}")
        c4.metric("Delayed Release Rate", f"{df['delayed_release_rate'].mean():.2%}")
        c5.metric("Peak Risk Count", int((df["period_type"] == "peak").sum()) if "period_type" in df.columns else 0)
    st.dataframe(df.head(20) if not df.empty else pd.DataFrame({"message": ["01_oms_order_flow.csv 없음"]}), use_container_width=True)
    if not df.empty and {"region_name", "order_count"}.issubset(df.columns):
        st.bar_chart(df.groupby("region_name")["order_count"].sum())
    if not df.empty and {"product_category", "order_count"}.issubset(df.columns):
        st.bar_chart(df.groupby("product_category")["order_count"].sum())
    st.info("**What this means**: delayed_release_rate가 높은 지역은 주문→출고 지시 병목 가능성이 높습니다.")
    st.success("**Recommended Action**: 피크 주간 OMS cut-off를 앞당기고 출고 wave를 증설하세요.")
    st.caption("**Data Caveat**: OMS 이벤트는 공개 물동량 기반 simulation layer입니다.")

with tabs[2]:
    st.subheader("WMS Dashboard")
    st.markdown("**Business Question**: 재고 부족/피킹 과부하 위험 SKU와 창고는 어디인가?")
    inv = cases["wms_inv"]
    pick = cases["wms_pick"]
    if not inv.empty and "stockout_risk_score" in inv.columns:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("High Stockout Risk Items", int((inv["stockout_risk_score"] > 0.3).sum()))
        c2.metric("Avg Stockout Risk", f"{inv['stockout_risk_score'].mean():.3f}")
        c3.metric("Max Warehouse Utilization", f"{pick['warehouse_utilization'].max():.2%}" if not pick.empty and "warehouse_utilization" in pick.columns else "N/A")
        c4.metric("High Workload Rows", int((pick["warehouse_utilization"] > 0.85).sum()) if not pick.empty and "warehouse_utilization" in pick.columns else 0)
        c5.metric("Reorder Priority Count", int((inv.get("reorder_priority", pd.Series(dtype=str)) == "High").sum()) if "reorder_priority" in inv.columns else 0)
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
    st.info("**What this means**: stockout_risk_score 상위 SKU는 피크 주간 품절 위험이 높습니다.")
    st.success("**Recommended Action**: 고위험 SKU 안전재고 20% 상향 + 긴급 reorder 트리거 적용.")
    st.caption("**Data Caveat**: 재고/피킹 지표는 simulation 기반이므로 실제 WMS 제약과 교차검증이 필요합니다.")

with tabs[3]:
    st.subheader("TMS Dashboard")
    st.markdown("**Business Question**: 어떤 지역에서 SLA 지연 리스크와 거리/차량부하 문제가 큰가?")
    st.caption("TMS는 공개 물동량 기반 simulation 데이터입니다.")
    df = cases["tms_sla"]
    if not df.empty and {"late_delivery_risk_score", "on_time_delivery_rate", "avg_route_distance_km", "avg_vehicle_utilization"}.issubset(df.columns):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Avg On-time Rate", f"{df['on_time_delivery_rate'].mean():.2%}")
        c2.metric("High SLA Risk Regions", int((df["late_delivery_risk_score"] > 0.2).sum()))
        c3.metric("Avg Vehicle Utilization", f"{df['avg_vehicle_utilization'].mean():.2%}")
        c4.metric("Avg Route Distance", f"{df['avg_route_distance_km'].mean():.2f} km")
        c5.metric("Cost per Delivery", "Proxy")
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
    st.info("**What this means**: SLA risk 상위 지역은 배송권역 재조정 및 임시 차량 슬롯 확보가 필요합니다.")
    st.success("**Recommended Action**: 고위험 권역 우선 배차 + 피크 시간 congestion 대응 룰 운영.")
    st.caption("**Data Caveat**: TMS 이벤트는 공개 물동량으로 생성한 simulation layer입니다.")

with tabs[4]:
    st.subheader("Forecasting & Regression")
    st.markdown("**Business Question**: 예측 오차를 줄여 capacity planning 신뢰도를 높일 수 있는가?")
    st.markdown("#### Forecasting (2023 test)")
    st.dataframe(forecast_metrics if not forecast_metrics.empty else pd.DataFrame({"message": ["forecasting metrics 없음"]}), use_container_width=True)
    if not forecast_pred.empty and {"date_key", "inbound_volume", "prediction"}.issubset(forecast_pred.columns):
        fp = forecast_pred.copy()
        fp["date_key"] = pd.to_datetime(fp["date_key"], errors="coerce")
        fp = fp[fp["date_key"].dt.year == 2023]
        if not fp.empty:
            ts = fp.groupby("date_key", as_index=False)[["inbound_volume", "prediction"]].sum()
            melted = ts.melt(id_vars="date_key", var_name="series", value_name="volume")
            st.altair_chart(
                alt.Chart(melted).mark_line().encode(
                    x=alt.X("date_key:T", title="Date"),
                    y=alt.Y("volume:Q", title="Daily volume"),
                    color=alt.Color("series:N", title="Series"),
                    tooltip=["date_key", "series", "volume"],
                ).properties(title="Actual vs Predicted (2023)"),
                use_container_width=True,
            )

    st.markdown("#### Regression")
    st.markdown("**Input features**: time, lag, rolling, entropy, distance proxy 등 (`feature_builder`)\n\n**Target**: `inbound_volume`.")
    st.dataframe(reg_metrics if not reg_metrics.empty else pd.DataFrame({"message": ["regression metrics 없음"]}), use_container_width=True)
    if not reg_metrics.empty and {"model", "wape"}.issubset(reg_metrics.columns):
        st.altair_chart(alt.Chart(reg_metrics).mark_bar().encode(x=alt.X("wape:Q", title="WAPE"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "wape"]), use_container_width=True)
        st.altair_chart(alt.Chart(reg_metrics).mark_bar().encode(x=alt.X("rmse:Q", title="RMSE"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "rmse"]), use_container_width=True)
        if "r2" in reg_metrics.columns:
            st.altair_chart(alt.Chart(reg_metrics).mark_bar(color="#4e79a7").encode(x=alt.X("r2:Q", title="R²"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "r2"]), use_container_width=True)
    elif not reg_metrics.empty and {"model", "WAPE"}.issubset(reg_metrics.columns):
        st.bar_chart(reg_metrics.set_index("model")[["WAPE", "R2"]])
    if not reg_pred.empty and {"y_true", "y_pred"}.issubset(reg_pred.columns):
        st.line_chart(reg_pred[["y_true", "y_pred"]].head(120))
        residual = reg_pred.copy()
        residual["residual"] = residual["y_true"] - residual["y_pred"]
        st.altair_chart(alt.Chart(residual.head(500)).mark_bar().encode(x=alt.X("residual:Q", bin=True, title="Residual"), y=alt.Y("count():Q", title="Count")), use_container_width=True)
    st.dataframe(reg_fi.head(20) if not reg_fi.empty else pd.DataFrame({"message": ["feature importance 없음"]}), use_container_width=True)
    st.info("**What this means**: WAPE가 낮은 모델을 운영계획에 우선 적용하고 고오차 구간은 별도 룰/재학습 대상으로 관리합니다.")
    st.caption("**Data Caveat**: 공개 물동량 기반 예측으로 실제 현장 이벤트와 차이가 있을 수 있습니다.")

with tabs[5]:
    st.subheader("Classification Analysis")
    st.markdown("**Input features**: feature_builder 산출 feature\n\n**Targets**: `peak_demand_risk`, `stockout_risk`, `late_delivery_risk`.")
    st.dataframe(cls_metrics if not cls_metrics.empty else pd.DataFrame({"message": ["classification metrics 없음"]}), use_container_width=True)
    if not cls_metrics.empty:
        metric_cols = [c for c in ["accuracy", "precision", "recall", "f1", "roc_auc"] if c in cls_metrics.columns]
        if metric_cols and (cls_metrics[metric_cols].fillna(0) >= 0.999).all().all():
            st.warning("분류 성능이 비정상적으로 높습니다. 데이터 누수 가능성을 점검하세요.")
    if not cls_metrics.empty and {"task", "f1"}.issubset(cls_metrics.columns):
        f1_df = cls_metrics.groupby("model", as_index=False)["f1"].mean().sort_values("f1", ascending=False)
        st.altair_chart(alt.Chart(f1_df).mark_bar().encode(x=alt.X("f1:Q", title="F1 score"), y=alt.Y("model:N", sort="-x"), tooltip=["model", "f1"]), use_container_width=True)
        best_model = f1_df.iloc[0]["model"] if not f1_df.empty else None
        if best_model and not cls_conf.empty and "model" in cls_conf.columns:
            st.markdown(f"**Best model confusion matrix: {best_model}**")
            st.dataframe(cls_conf[cls_conf["model"] == best_model], use_container_width=True)
    st.dataframe(cls_conf if not cls_conf.empty else pd.DataFrame({"message": ["confusion_matrix 없음"]}), use_container_width=True)
    st.dataframe(cls_fi.head(20) if not cls_fi.empty else pd.DataFrame({"message": ["classification feature importance 없음"]}), use_container_width=True)

with tabs[6]:
    st.subheader("Statistical Analysis")
    st.markdown("p-value < 0.05이면 유의하다고 보되 effect size와 비즈니스 의미를 함께 해석합니다.")
    st.dataframe(stat_tests if not stat_tests.empty else pd.DataFrame({"message": ["statistical_tests 없음"]}), use_container_width=True)
    st.dataframe(stat_effect if not stat_effect.empty else pd.DataFrame({"message": ["effect_sizes 없음"]}), use_container_width=True)
    if not stat_group.empty:
        st.dataframe(stat_group, use_container_width=True)

with tabs[7]:
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

with tabs[8]:
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

with tabs[9]:
    st.subheader("Recommendation")
    st.markdown("이커머스 지수는 본 PoC의 지역 특성 proxy feature(합성/외생 지표)로 사용됩니다.")
    st.dataframe(cases["locker"].head(20) if not cases["locker"].empty else pd.DataFrame({"message": ["08_case 없음"]}), use_container_width=True)

with tabs[10]:
    st.subheader("Optimization Formulation")
    st.markdown(opt_form)
    st.markdown("- $d_{ij}$: 노드 i→j 거리\n- $x_{ijk}$: 차량 k가 i→j 이동하면 1\n- 예시: `route_plan.csv`의 vehicle별 stop 이동이 $x_{ijk}$에 대응")
    st.latex(r"\min \sum_{k \in K} \sum_{i \in V}\sum_{j \in V, j\neq i} d_{ij} x_{ijk}")
    st.latex(r"\min x^TQx")
    if not route_plan.empty:
        st.markdown("### Suggested Route Order (from route_plan)")
        st.dataframe(route_plan.sort_values(["vehicle_id"]).head(100), use_container_width=True)

with tabs[11]:
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

with tabs[12]:
    st.subheader("Data Dictionary")
    st.markdown(data_spec_md)
