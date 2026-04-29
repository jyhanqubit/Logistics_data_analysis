from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .db import query_df


def _safe_smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denominator = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    mask = denominator != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denominator[mask]))


def _wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return 0.0
    return float(np.sum(np.abs(y_true - y_pred)) / denom)


def load_forecasting_dataset(db_path: Path) -> pd.DataFrame:
    df = query_df(db_path, """
        SELECT
            f.date_key,
            f.dest_region_id,
            r.region_name,
            r.population,
            r.ecommerce_index,
            r.income_index,
            f.category_id,
            c.category_name,
            c.perishability_score,
            c.bulky_score,
            f.inbound_volume
        FROM fact_daily_demand f
        JOIN dim_region r ON f.dest_region_id = r.region_id
        JOIN dim_category c ON f.category_id = c.category_id
        ORDER BY f.dest_region_id, f.category_id, f.date_key
    """)
    df["date_key"] = pd.to_datetime(df["date_key"])
    iso = df["date_key"].dt.isocalendar()
    df["month"] = df["date_key"].dt.month.astype(int)
    df["day_of_week"] = df["date_key"].dt.dayofweek.astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_holiday"] = 0
    df["week_of_year"] = iso.week.astype(int)
    return df


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["dest_region_id", "category_id", "date_key"]).copy()
    group_cols = ["dest_region_id", "category_id"]
    df["lag_1"] = df.groupby(group_cols)["inbound_volume"].shift(1)
    df["lag_7"] = df.groupby(group_cols)["inbound_volume"].shift(7)
    df["lag_14"] = df.groupby(group_cols)["inbound_volume"].shift(14)
    df["rolling_7_mean"] = df.groupby(group_cols)["inbound_volume"].transform(lambda s: s.shift(1).rolling(7).mean())
    df["rolling_14_mean"] = df.groupby(group_cols)["inbound_volume"].transform(lambda s: s.shift(1).rolling(14).mean())
    df["day_index"] = (df["date_key"] - df["date_key"].min()).dt.days
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df = df.dropna().reset_index(drop=True)
    return df


FEATURE_COLUMNS = [
    "dest_region_id",
    "category_id",
    "population",
    "ecommerce_index",
    "income_index",
    "perishability_score",
    "bulky_score",
    "month",
    "day_of_week",
    "is_weekend",
    "is_holiday",
    "week_of_year",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_7_mean",
    "rolling_14_mean",
    "day_index",
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
]


def run_forecasting(db_path: Path, output_dir: Path, model_dir: Path, test_days: int = 28) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    raw = load_forecasting_dataset(db_path)
    df = make_features(raw)
    unique_days = int(df["date_key"].nunique())
    adaptive_test_days = min(test_days, max(1, unique_days // 3))
    cutoff = df["date_key"].max() - pd.Timedelta(days=adaptive_test_days - 1)
    train = df[df["date_key"] < cutoff].copy()
    test = df[df["date_key"] >= cutoff].copy()
    if train.empty or test.empty:
        if len(df) < 2:
            raise ValueError("Not enough rows for forecasting after feature engineering.")
        split_idx = max(1, int(len(df) * 0.8))
        train = df.iloc[:split_idx].copy()
        test = df.iloc[split_idx:].copy()
        if test.empty:
            test = df.iloc[-1:].copy()
            train = df.iloc[:-1].copy()
        if train.empty or test.empty:
            raise ValueError("Not enough data for temporal split after adaptive fallback.")

    models = {
        "linear_regression": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "random_forest": RandomForestRegressor(n_estimators=140, random_state=42),
        "gradient_boosting": GradientBoostingRegressor(random_state=42, n_estimators=180, learning_rate=0.05, max_depth=3),
        "hist_gradient_boosting": HistGradientBoostingRegressor(random_state=42),
    }
    predictions: dict[str, np.ndarray] = {}
    for name, model in models.items():
        model.fit(train[FEATURE_COLUMNS], train["inbound_volume"])
        predictions[name] = np.maximum(0, model.predict(test[FEATURE_COLUMNS])).round(2)

    # Seasonal naive baseline: lag_7
    test["seasonal_naive"] = test["lag_7"].clip(lower=0)
    y_true = test["inbound_volume"].to_numpy()
    y_pred = predictions["gradient_boosting"]
    y_base = test["seasonal_naive"].to_numpy()

    metric_rows = [
        {
            "model": "seasonal_naive_lag7",
            "mae": mean_absolute_error(y_true, y_base),
            "rmse": float(np.sqrt(mean_squared_error(y_true, y_base))),
            "wape": _wape(y_true, y_base),
            "smape": _safe_smape(y_true, y_base),
        }
    ]
    for name, pred in predictions.items():
        metric_rows.append(
            {
                "model": name,
                "mae": mean_absolute_error(y_true, pred),
                "rmse": float(np.sqrt(mean_squared_error(y_true, pred))),
                "wape": _wape(y_true, pred),
                "smape": _safe_smape(y_true, pred),
            }
        )
    metrics = pd.DataFrame(metric_rows)
    metrics[["mae", "rmse", "wape", "smape"]] = metrics[["mae", "rmse", "wape", "smape"]].round(4)

    gbm = models["gradient_boosting"]
    feature_importance = pd.DataFrame({"feature": FEATURE_COLUMNS, "importance": gbm.feature_importances_}).sort_values("importance", ascending=False)

    pred_cols = [
        "date_key", "dest_region_id", "region_name", "category_id", "category_name",
        "inbound_volume", "prediction", "seasonal_naive"
    ]
    for name, pred in predictions.items():
        test[f"pred_{name}"] = pred
    test["prediction"] = predictions["gradient_boosting"]
    test[pred_cols].to_csv(output_dir / "forecast_predictions.csv", index=False, encoding="utf-8-sig")
    metrics.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")
    feature_importance.to_csv(output_dir / "feature_importance.csv", index=False, encoding="utf-8-sig")
    joblib.dump({"model": gbm, "features": FEATURE_COLUMNS}, model_dir / "demand_forecast_gbr.joblib")

    best = metrics.sort_values("wape").iloc[0]
    gbm = metrics[metrics["model"] == "gradient_boosting"].iloc[0]
    base = metrics[metrics["model"] == "seasonal_naive_lag7"].iloc[0]
    improvement = (float(base["wape"]) - float(gbm["wape"])) / float(base["wape"]) if float(base["wape"]) > 0 else 0.0
    summary = f"""
# 수요예측 요약

## 모델 비교

- Best model by WAPE: **{best['model']}**
- Seasonal naive WAPE: **{float(base['wape']):.2%}**
- Gradient Boosting WAPE: **{float(gbm['wape']):.2%}**
- WAPE 개선율: **{improvement:.2%}**

## 해석

`지역 × 상품군 × 일자` 단위 물동량을 예측했습니다. Gradient Boosting 모델은 요일성, 월별 시즌성, 지역별 이커머스 지수, 직전 1/7/14일 lag, rolling mean을 사용합니다. 실제 공개데이터 연결 시 동일한 feature engineering과 temporal backtest 구조를 유지하면 됩니다.
""".lstrip()
    (output_dir / "forecast_summary.md").write_text(summary, encoding="utf-8")

    return {
        "metrics": metrics,
        "predictions": test[pred_cols],
        "feature_importance": feature_importance,
        "model_path": model_dir / "demand_forecast_gbr.joblib",
    }
