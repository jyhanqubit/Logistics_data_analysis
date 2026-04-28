from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

st.set_page_config(page_title="ParcelFlow AI PoC", layout="wide")
st.title("ParcelFlow AI — 생활물류 분석 PoC")
st.caption("SCM 분석 · 수요예측 · 후보지 추천 · 최적화 실험")

required = [
    OUTPUTS / "forecasting" / "model_metrics.csv",
    OUTPUTS / "recommender" / "site_recommendations.csv",
    OUTPUTS / "scm" / "region_volatility.csv",
]
if not all(p.exists() for p in required):
    st.warning("먼저 `python scripts/run_pipeline.py`를 실행해 outputs/를 생성하세요.")
    st.stop()

metrics = pd.read_csv(OUTPUTS / "forecasting" / "model_metrics.csv")
rec = pd.read_csv(OUTPUTS / "recommender" / "site_recommendations.csv")
vol = pd.read_csv(OUTPUTS / "scm" / "region_volatility.csv")

c1, c2, c3 = st.columns(3)
gbm = metrics[metrics["model"] == "gradient_boosting"].iloc[0]
c1.metric("Forecast WAPE", f"{gbm['wape']:.2%}")
c2.metric("추천 후보 지역 수", f"{rec['region_name'].nunique()}개")
c3.metric("총 분석 지역", f"{vol['region_name'].nunique()}개")

st.header("수요예측 모델 성능")
st.dataframe(metrics, use_container_width=True)

st.header("거점/락커 추천 Top 10")
selected_type = st.selectbox("추천 유형", sorted(rec["recommendation_type"].unique()))
st.dataframe(
    rec[rec["recommendation_type"] == selected_type].sort_values("rank").head(10),
    use_container_width=True,
)

st.header("지역별 총 물동량/변동성")
st.dataframe(vol.sort_values("total_volume", ascending=False).head(15), use_container_width=True)

route_path = OUTPUTS / "optimization" / "route_plan.csv"
if route_path.exists():
    st.header("배송 경로 최적화 결과")
    st.dataframe(pd.read_csv(route_path), use_container_width=True)

qubo_path = OUTPUTS / "optimization" / "qubo_solution.csv"
if qubo_path.exists():
    st.header("QUBO 거점 선택 실험")
    st.dataframe(pd.read_csv(qubo_path).head(10), use_container_width=True)

st.header("Operations (OMS/WMS/TMS) KPI")
ops_dir = OUTPUTS / "ops_simulation"
ops_files = {
    "OMS KPI": ops_dir / "oms_kpi.csv",
    "WMS KPI": ops_dir / "wms_kpi.csv",
    "TMS KPI": ops_dir / "tms_kpi.csv",
}
if all(path.exists() for path in ops_files.values()):
    tab_oms, tab_wms, tab_tms = st.tabs(["OMS KPI", "WMS KPI", "TMS KPI"])
    with tab_oms:
        st.dataframe(pd.read_csv(ops_files["OMS KPI"]), use_container_width=True)
    with tab_wms:
        st.dataframe(pd.read_csv(ops_files["WMS KPI"]), use_container_width=True)
    with tab_tms:
        st.dataframe(pd.read_csv(ops_files["TMS KPI"]), use_container_width=True)
else:
    st.info("operations KPI 파일이 없습니다. 먼저 `python scripts/run_pipeline.py`를 실행해 outputs/ops_simulation/을 생성하세요.")
