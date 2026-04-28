from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data_generator import haversine_km
from .db import query_df


def _minmax(series: pd.Series) -> pd.Series:
    lo = series.min()
    hi = series.max()
    if hi == lo:
        return pd.Series(np.ones(len(series)), index=series.index)
    return (series - lo) / (hi - lo)


def run_site_recommender(db_path: Path, forecast_predictions_path: Path, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(forecast_predictions_path)
    pred["date_key"] = pd.to_datetime(pred["date_key"])

    region_pred = pred.groupby(["dest_region_id", "region_name"], as_index=False).agg(
        forecast_volume=("prediction", "sum"),
        actual_volume=("inbound_volume", "sum"),
        avg_prediction=("prediction", "mean"),
    )

    # 최근 4주 예측 수요와 전체 실적/변동성을 결합
    actual = query_df(db_path, """
        SELECT
            f.date_key,
            f.dest_region_id,
            r.region_name,
            r.lat,
            r.lon,
            r.population,
            r.ecommerce_index,
            r.income_index,
            SUM(f.inbound_volume) AS daily_volume
        FROM fact_daily_demand f
        JOIN dim_region r ON f.dest_region_id = r.region_id
        GROUP BY 1,2,3,4,5,6,7,8
    """)
    actual["date_key"] = pd.to_datetime(actual["date_key"])
    trend = actual.sort_values("date_key").copy()
    first_half = trend[trend["date_key"] <= trend["date_key"].min() + (trend["date_key"].max() - trend["date_key"].min()) / 2]
    second_half = trend[trend["date_key"] > trend["date_key"].min() + (trend["date_key"].max() - trend["date_key"].min()) / 2]
    growth = (
        second_half.groupby("dest_region_id")["daily_volume"].mean()
        / first_half.groupby("dest_region_id")["daily_volume"].mean()
        - 1
    ).replace([np.inf, -np.inf], 0).fillna(0).reset_index(name="growth_rate")

    volatility = actual.groupby("dest_region_id")["daily_volume"].agg(["std", "mean"]).reset_index()
    volatility["cv"] = volatility["std"] / volatility["mean"]
    region_meta = actual.groupby(["dest_region_id", "region_name", "lat", "lon", "population", "ecommerce_index", "income_index"], as_index=False)["daily_volume"].sum()
    hub_meta = query_df(db_path, "SELECT hub_name, lat, lon FROM dim_hub_candidate")

    def nearest_hub_distance(row: pd.Series) -> float:
        return min(haversine_km(row["lat"], row["lon"], h["lat"], h["lon"]) for _, h in hub_meta.iterrows())

    candidates = region_meta.merge(region_pred, on=["dest_region_id", "region_name"], how="left")
    candidates = candidates.merge(growth, on="dest_region_id", how="left")
    candidates = candidates.merge(volatility[["dest_region_id", "cv"]], on="dest_region_id", how="left")
    candidates["forecast_volume"] = candidates["forecast_volume"].fillna(0)
    candidates["growth_rate"] = candidates["growth_rate"].fillna(0)
    candidates["cv"] = candidates["cv"].fillna(0)
    candidates["nearest_hub_distance_km"] = candidates.apply(nearest_hub_distance, axis=1)

    candidates["score_demand"] = _minmax(candidates["forecast_volume"])
    candidates["score_growth"] = _minmax(candidates["growth_rate"])
    candidates["score_volatility"] = _minmax(candidates["cv"])
    candidates["score_ecommerce"] = _minmax(candidates["ecommerce_index"])
    candidates["score_distance_gap"] = _minmax(candidates["nearest_hub_distance_km"])
    candidates["score_population"] = _minmax(candidates["population"])

    candidates["micro_fulfillment_score"] = (
        0.36 * candidates["score_demand"]
        + 0.20 * candidates["score_growth"]
        + 0.14 * candidates["score_distance_gap"]
        + 0.14 * candidates["score_ecommerce"]
        + 0.10 * candidates["score_population"]
        - 0.06 * candidates["score_volatility"]
    )
    candidates["locker_score"] = (
        0.42 * candidates["score_demand"]
        + 0.18 * candidates["score_ecommerce"]
        + 0.16 * candidates["score_population"]
        + 0.14 * candidates["score_growth"]
        + 0.10 * candidates["score_volatility"]
    )

    def reason(row: pd.Series, target: str) -> str:
        parts = []
        if row["score_demand"] >= 0.75:
            parts.append("예측 물동량 상위권")
        if row["score_growth"] >= 0.65:
            parts.append("최근 수요 증가율 높음")
        if row["score_distance_gap"] >= 0.65 and target == "MFC":
            parts.append("기존 허브와 거리 gap 존재")
        if row["score_ecommerce"] >= 0.70:
            parts.append("이커머스 지수 높음")
        if row["score_volatility"] >= 0.70 and target == "Locker":
            parts.append("피크 변동성 대응 필요")
        return "; ".join(parts) or "균형형 후보"

    mfc = candidates.copy()
    mfc["recommendation_type"] = "Micro Fulfillment Center"
    mfc["score"] = mfc["micro_fulfillment_score"]
    mfc["reason"] = mfc.apply(lambda r: reason(r, "MFC"), axis=1)

    locker = candidates.copy()
    locker["recommendation_type"] = "Parcel Locker"
    locker["score"] = locker["locker_score"]
    locker["reason"] = locker.apply(lambda r: reason(r, "Locker"), axis=1)

    combined = pd.concat([mfc, locker], ignore_index=True)
    combined = combined.sort_values(["recommendation_type", "score"], ascending=[True, False])
    combined["rank"] = combined.groupby("recommendation_type")["score"].rank(ascending=False, method="first").astype(int)

    cols = [
        "recommendation_type", "rank", "region_name", "score", "forecast_volume", "growth_rate", "cv",
        "nearest_hub_distance_km", "ecommerce_index", "population", "reason"
    ]
    result = combined[cols].sort_values(["recommendation_type", "rank"])
    result["score"] = result["score"].round(4)
    result["forecast_volume"] = result["forecast_volume"].round(0).astype(int)
    result["growth_rate"] = result["growth_rate"].round(4)
    result["cv"] = result["cv"].round(4)
    result["nearest_hub_distance_km"] = result["nearest_hub_distance_km"].round(2)

    result.to_csv(output_dir / "site_recommendations.csv", index=False, encoding="utf-8-sig")

    top_mfc = result[result["recommendation_type"] == "Micro Fulfillment Center"].iloc[0]
    top_locker = result[result["recommendation_type"] == "Parcel Locker"].iloc[0]
    summary = f"""
# 추천 시스템 요약

## Top recommendations

- MFC 1순위: **{top_mfc['region_name']}** / score {float(top_mfc['score']):.3f} / {top_mfc['reason']}
- 택배락커 1순위: **{top_locker['region_name']}** / score {float(top_locker['score']):.3f} / {top_locker['reason']}

## 모델 설명

추천 점수는 예측 물동량, 최근 성장률, 수요 변동성, 이커머스 지수, 인구, 기존 허브와의 거리 gap을 결합한 weighted ranking입니다. 실제 프로젝트에서는 SHAP 기반 설명 또는 learning-to-rank 모델로 확장할 수 있습니다.
""".lstrip()
    (output_dir / "recommendation_summary.md").write_text(summary, encoding="utf-8")
    return result
