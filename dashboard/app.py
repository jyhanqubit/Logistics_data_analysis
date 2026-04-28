from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DOCS = ROOT / "docs" / "dashboard"


st.set_page_config(page_title="ParcelFlow AI Portfolio Dashboard", layout="wide")
st.title("ParcelFlow AI — Professional Portfolio Dashboard")
st.caption("공개 생활물류 데이터 기반 분석 + OMS/WMS/TMS simulation layer + quantum-ready QUBO PoC")


def _read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.warning(f"파일을 읽을 수 없습니다: {path.name} ({exc})")
        return pd.DataFrame()


def _read_text_safe(path: Path, fallback: str) -> str:
    if not path.exists():
        return fallback
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return fallback


# data loading
metrics = _read_csv_safe(OUTPUTS / "forecasting" / "model_metrics.csv")
forecast_pred = _read_csv_safe(OUTPUTS / "forecasting" / "forecast_predictions.csv")
rec = _read_csv_safe(OUTPUTS / "recommender" / "site_recommendations.csv")
vol = _read_csv_safe(OUTPUTS / "scm" / "region_volatility.csv")
route = _read_csv_safe(OUTPUTS / "optimization" / "route_plan.csv")
qubo_sol = _read_csv_safe(OUTPUTS / "optimization" / "qubo_solution.csv")
qubo_mat = _read_csv_safe(OUTPUTS / "optimization" / "qubo_matrix.csv")
oms_kpi = _read_csv_safe(OUTPUTS / "ops_simulation" / "oms_kpi.csv")
wms_kpi = _read_csv_safe(OUTPUTS / "ops_simulation" / "wms_kpi.csv")
tms_kpi = _read_csv_safe(OUTPUTS / "ops_simulation" / "tms_kpi.csv")

biz_impact_md = _read_text_safe(DOCS / "dashboard_business_impact.md", "Business impact 문서가 없습니다.")
col_dict_md = _read_text_safe(DOCS / "dashboard_column_dictionary.md", "Column dictionary 문서가 없습니다.")
route_interp_md = _read_text_safe(DOCS / "route_optimization_interpretation.md", "Route interpretation 문서가 없습니다.")
qubo_explain_md = _read_text_safe(DOCS / "quantum_qubo_explanation.md", "QUBO 설명 문서가 없습니다.")
ops_guide_md = _read_text_safe(DOCS / "operations_kpi_guide.md", "Operations KPI 가이드 문서가 없습니다.")
vis_plan_md = _read_text_safe(DOCS / "dashboard_visualization_plan.md", "Visualization plan 문서가 없습니다.")
casebook_points_md = _read_text_safe(DOCS / "dashboard_casebook_talking_points.md", "Talking points 문서가 없습니다.")

st.info(
    "주의: 본 대시보드는 공개 생활물류/택배 물동량 데이터 기반 분석입니다. "
    "OMS/WMS/TMS 이벤트는 simulation layer이며, QUBO는 quantum-ready formulation의 classical 검증 결과입니다."
)

tabs = st.tabs(
    [
        "1) Business Impact",
        "2) Data & Columns",
        "3) SCM Analytics",
        "4) Forecasting",
        "5) Recommendation",
        "6) Route Optimization",
        "7) QUBO / Quantum PoC",
        "8) Operations KPI",
        "9) Casebook / Talking Points",
    ]
)

with tabs[0]:
    st.subheader("Business Impact")
    st.markdown(biz_impact_md)

    c1, c2, c3 = st.columns(3)
    if not metrics.empty and "wape" in metrics.columns:
        gbm = metrics.loc[metrics["model"].astype(str).str.contains("gradient", case=False, na=False)]
        c1.metric("Best WAPE", f"{float(gbm['wape'].iloc[0]):.2%}" if not gbm.empty else "N/A")
    else:
        c1.metric("Best WAPE", "N/A")
    c2.metric("추천 후보 지역 수", f"{rec['region_name'].nunique()}" if "region_name" in rec.columns else "N/A")
    c3.metric("SCM 분석 지역 수", f"{vol['region_name'].nunique()}" if "region_name" in vol.columns else "N/A")

with tabs[1]:
    st.subheader("Data & Columns")
    st.markdown(col_dict_md)
    st.markdown("### Visualization Plan")
    st.markdown(vis_plan_md)

with tabs[2]:
    st.subheader("SCM Analytics")
    if vol.empty:
        st.warning("`outputs/scm/region_volatility.csv`가 없어 SCM 시각화를 표시할 수 없습니다.")
    else:
        sort_col = "total_volume" if "total_volume" in vol.columns else vol.columns[0]
        st.dataframe(vol.sort_values(sort_col, ascending=False).head(20), use_container_width=True)
        if {"region_name", "total_volume"}.issubset(vol.columns):
            st.bar_chart(vol.set_index("region_name")["total_volume"].head(15))

with tabs[3]:
    st.subheader("Forecasting")
    if metrics.empty:
        st.warning("`outputs/forecasting/model_metrics.csv`가 없어 성능 지표를 표시할 수 없습니다.")
    else:
        st.dataframe(metrics, use_container_width=True)
    if not forecast_pred.empty and {"date_key", "y_true", "y_pred"}.issubset(forecast_pred.columns):
        chart_df = forecast_pred[["date_key", "y_true", "y_pred"]].copy().tail(90)
        chart_df["date_key"] = pd.to_datetime(chart_df["date_key"], errors="coerce")
        chart_df = chart_df.dropna(subset=["date_key"]).set_index("date_key")
        st.line_chart(chart_df)

with tabs[4]:
    st.subheader("Recommendation")
    if rec.empty:
        st.warning("`outputs/recommender/site_recommendations.csv`가 없어 추천 결과를 표시할 수 없습니다.")
    else:
        if "recommendation_type" in rec.columns:
            options = sorted(rec["recommendation_type"].dropna().unique().tolist())
            selected = st.selectbox("추천 유형", options)
            rec_view = rec[rec["recommendation_type"] == selected]
        else:
            rec_view = rec
        st.dataframe(rec_view.sort_values("rank").head(20) if "rank" in rec_view.columns else rec_view.head(20), use_container_width=True)

with tabs[5]:
    st.subheader("Route Optimization")
    st.markdown(route_interp_md)
    if route.empty:
        st.warning("`outputs/optimization/route_plan.csv`가 없어 경로 최적화 결과를 표시할 수 없습니다.")
    else:
        st.dataframe(route, use_container_width=True)

with tabs[6]:
    st.subheader("QUBO / Quantum PoC")
    st.markdown(qubo_explain_md)

    if qubo_sol.empty:
        st.warning("`outputs/optimization/qubo_solution.csv`가 없어 QUBO 결과를 표시할 수 없습니다.")
    else:
        st.dataframe(qubo_sol.head(20), use_container_width=True)

    if not qubo_mat.empty:
        st.markdown("### QUBO Matrix")
        st.dataframe(qubo_mat, use_container_width=True)
        st.caption("QUBO matrix가 5x5이고 bitstring 길이가 5이면 5개 binary variable 문제로 해석합니다.")

with tabs[7]:
    st.subheader("Operations KPI")
    st.markdown(ops_guide_md)

    c_oms, c_wms, c_tms = st.columns(3)
    with c_oms:
        st.markdown("#### OMS KPI")
        st.dataframe(oms_kpi if not oms_kpi.empty else pd.DataFrame({"message": ["파일 없음"]}), use_container_width=True)
    with c_wms:
        st.markdown("#### WMS KPI")
        st.dataframe(wms_kpi if not wms_kpi.empty else pd.DataFrame({"message": ["파일 없음"]}), use_container_width=True)
    with c_tms:
        st.markdown("#### TMS KPI")
        st.dataframe(tms_kpi if not tms_kpi.empty else pd.DataFrame({"message": ["파일 없음"]}), use_container_width=True)

with tabs[8]:
    st.subheader("Casebook / Talking Points")
    st.markdown(casebook_points_md)

    casebook_path = ROOT / "analysis_cases" / "README.md"
    if casebook_path.exists():
        st.markdown("### Analysis Casebook")
        st.markdown(casebook_path.read_text(encoding="utf-8"))
    else:
        st.warning("analysis_cases/README.md가 없습니다.")
