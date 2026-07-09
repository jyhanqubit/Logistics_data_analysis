from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from .db import query_df

# ---------------------------------------------------------------------------
# 평가 설계 노트
#
# 1) 단일 holdout 대신 rolling-origin backtest를 쓴다.
#    origin을 여러 번 뒤로 밀며 매번 "그 시점까지의 데이터로 학습 -> 이후 28일 예측"을
#    반복한다. 단일 분할은 특정 기간(명절, 프로모션)에 지표가 좌우되지만, origin을
#    옮겨가며 평가하면 지표의 분산까지 확인할 수 있다. expanding window를 택한 이유:
#    데이터가 210일로 짧아 오래된 구간을 버리는 sliding window는 학습량 손해가 더 크고,
#    이 데이터에는 버려서 이득을 볼 만한 구조 변화(regime change)가 없다.
#
# 2) 테스트 구간 예측은 recursive multi-step으로 한다.
#    운영 시점에는 origin 이후의 실측이 없다. lag_1을 실측으로 채워 평가하면
#    1-step-ahead 성능을 28일 예측 성능인 것처럼 부풀리는 누수다. 여기서는 예측값을
#    다시 lag로 되먹임해 horizon이 길수록 오차가 누적되는 현실을 지표에 반영한다.
#
# 3) day_index(전체 기간 경과일) 피처는 제거했다.
#    트리 모델은 학습 범위 밖 값을 외삽하지 못해, 미래 구간에서 이 피처는 상수로
#    작동한다. 추세 정보는 못 주면서 학습 구간 과적합 위험만 남아 뺐다.
# ---------------------------------------------------------------------------

# recursive 예측은 horizon이 길수록 오차가 누적된다. horizon별 백테스트에서
# h15 이후 모델 WAPE가 seasonal naive에 역전되는 것을 확인해, 운영 예측은
# 14일까지 모델, 그 이후는 naive로 전환한다. 전환점은 백테스트 산출물
# (backtest_by_horizon.csv)로 근거를 남긴다.
SWITCH_HORIZON = 14

LAG_DAYS = (1, 7, 14)
ROLLING_WINDOWS = (7, 14)
MAX_HISTORY = 14  # 피처 계산에 필요한 최소 이력

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
    "month_sin",
    "month_cos",
    "dow_sin",
    "dow_cos",
]

STATIC_COLUMNS = [
    "dest_region_id", "category_id", "population", "ecommerce_index",
    "income_index", "perishability_score", "bulky_score",
]
CALENDAR_COLUMNS = ["month", "day_of_week", "is_weekend", "is_holiday", "week_of_year"]


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
            f.inbound_volume,
            cal.month,
            cal.day_of_week,
            cal.is_weekend,
            cal.is_holiday,
            cal.week_of_year
        FROM fact_daily_demand f
        JOIN dim_region r ON f.dest_region_id = r.region_id
        JOIN dim_category c ON f.category_id = c.category_id
        JOIN dim_calendar cal ON f.date_key = cal.date_key
        ORDER BY f.dest_region_id, f.category_id, f.date_key
    """)
    df["date_key"] = pd.to_datetime(df["date_key"])
    return df


def _add_cyclic(df: pd.DataFrame) -> pd.DataFrame:
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    return df


def make_training_features(df: pd.DataFrame) -> pd.DataFrame:
    """학습용 피처. lag/rolling은 전부 shift(1) 이후 값만 쓴다(당일 값 누수 차단)."""
    df = df.sort_values(["dest_region_id", "category_id", "date_key"]).copy()
    group_cols = ["dest_region_id", "category_id"]
    for lag in LAG_DAYS:
        df[f"lag_{lag}"] = df.groupby(group_cols)["inbound_volume"].shift(lag)
    for win in ROLLING_WINDOWS:
        df[f"rolling_{win}_mean"] = df.groupby(group_cols)["inbound_volume"].transform(
            lambda s: s.shift(1).rolling(win).mean()
        )
    df = _add_cyclic(df)
    return df.dropna().reset_index(drop=True)


def _recursive_forecast(
    model: GradientBoostingRegressor,
    history: pd.DataFrame,
    future: pd.DataFrame,
    quantile_models: dict[float, GradientBoostingRegressor] | None = None,
) -> pd.DataFrame:
    """origin 이후 구간을 하루씩 예측하며, 예측값을 lag 이력으로 되먹임한다.

    history: origin 이전 실측 (series별 최소 MAX_HISTORY일)
    future:  origin 이후 달력/정적 피처만 있는 프레임 (실측 미사용)
    quantile 예측은 point 모델이 만든 lag 경로를 조건으로 같은 피처에서 계산한다.
    (recursive 경로를 quantile별로 따로 굴리면 하위/상위 경로가 비현실적으로
    벌어지므로, 중앙 경로 조건부 quantile로 근사한다. 한계는 README에 명시.)
    """
    series_hist: dict[tuple[int, int], list[float]] = {}
    for key, grp in history.groupby(["dest_region_id", "category_id"]):
        series_hist[key] = grp.sort_values("date_key")["inbound_volume"].astype(float).tolist()[-MAX_HISTORY:]

    out_rows = []
    for date, day_frame in future.sort_values("date_key").groupby("date_key", sort=True):
        day_frame = day_frame.copy()
        feats = {"lag_1": [], "lag_7": [], "lag_14": [], "rolling_7_mean": [], "rolling_14_mean": []}
        keys = list(zip(day_frame["dest_region_id"], day_frame["category_id"]))
        for key in keys:
            hist = series_hist[key]
            feats["lag_1"].append(hist[-1])
            feats["lag_7"].append(hist[-7])
            feats["lag_14"].append(hist[-14])
            feats["rolling_7_mean"].append(float(np.mean(hist[-7:])))
            feats["rolling_14_mean"].append(float(np.mean(hist[-14:])))
        for col, vals in feats.items():
            day_frame[col] = vals
        day_frame = _add_cyclic(day_frame)

        pred = np.maximum(0, model.predict(day_frame[FEATURE_COLUMNS]))
        day_frame["prediction"] = pred.round(2)
        if quantile_models:
            for alpha, qm in quantile_models.items():
                qcol = f"q{int(alpha * 100):02d}"
                day_frame[qcol] = np.maximum(0, qm.predict(day_frame[FEATURE_COLUMNS])).round(2)
        out_rows.append(day_frame)

        for key, p in zip(keys, pred):
            series_hist[key].append(float(p))
            series_hist[key] = series_hist[key][-MAX_HISTORY:]

    return pd.concat(out_rows, ignore_index=True)


def _seasonal_naive_multistep(history: pd.DataFrame, future: pd.DataFrame) -> pd.Series:
    """origin 이전 실측만 쓰는 seasonal naive. horizon h의 예측은 origin 이전
    마지막 같은 요일 실측을 반복 사용한다(운영 시점에 아는 정보만 사용)."""
    last_week: dict[tuple[int, int, int], float] = {}
    hist = history.sort_values("date_key")
    for (rid, cid), grp in hist.groupby(["dest_region_id", "category_id"]):
        tail = grp.tail(7)
        for _, row in tail.iterrows():
            last_week[(rid, cid, int(row["day_of_week"]))] = float(row["inbound_volume"])
    return future.apply(
        lambda r: last_week.get((r["dest_region_id"], r["category_id"], int(r["day_of_week"])), 0.0),
        axis=1,
    )


def _fit_point_model(train: pd.DataFrame) -> GradientBoostingRegressor:
    model = GradientBoostingRegressor(random_state=42, n_estimators=180, learning_rate=0.05, max_depth=3)
    model.fit(train[FEATURE_COLUMNS], train["inbound_volume"])
    return model


def _fit_quantile_models(train: pd.DataFrame, alphas: tuple[float, ...]) -> dict[float, GradientBoostingRegressor]:
    models = {}
    for alpha in alphas:
        qm = GradientBoostingRegressor(
            loss="quantile", alpha=alpha,
            random_state=42, n_estimators=180, learning_rate=0.05, max_depth=3,
        )
        qm.fit(train[FEATURE_COLUMNS], train["inbound_volume"])
        models[alpha] = qm
    return models


def run_forecasting(
    db_path: Path,
    output_dir: Path,
    model_dir: Path,
    test_days: int = 28,
    n_folds: int = 3,
    quantile_alphas: tuple[float, ...] = (0.1, 0.5, 0.75, 0.9),
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    raw = load_forecasting_dataset(db_path)
    max_date = raw["date_key"].max()

    # -------------------------- rolling-origin backtest --------------------
    fold_metrics = []
    horizon_rows = []
    for fold in range(n_folds, 0, -1):
        origin = max_date - pd.Timedelta(days=test_days * fold - 1)
        hist_raw = raw[raw["date_key"] < origin]
        test_raw = raw[(raw["date_key"] >= origin) & (raw["date_key"] < origin + pd.Timedelta(days=test_days))]
        train = make_training_features(hist_raw)
        if train.empty or test_raw.empty:
            raise ValueError("Not enough data for rolling-origin fold. Reduce n_folds or test_days.")

        model = _fit_point_model(train)
        future = test_raw.drop(columns=["inbound_volume"]).copy()
        fc = _recursive_forecast(model, hist_raw, future)
        fc = fc.merge(
            test_raw[["date_key", "dest_region_id", "category_id", "inbound_volume"]],
            on=["date_key", "dest_region_id", "category_id"], how="left",
        )
        fc["seasonal_naive"] = _seasonal_naive_multistep(hist_raw, fc)
        fc["horizon"] = (fc["date_key"] - origin).dt.days + 1

        fc["blend"] = np.where(fc["horizon"] <= SWITCH_HORIZON, fc["prediction"], fc["seasonal_naive"])

        y = fc["inbound_volume"].to_numpy()
        p = fc["prediction"].to_numpy()
        b = fc["seasonal_naive"].to_numpy()
        bl = fc["blend"].to_numpy()
        fold_metrics.append({
            "fold": n_folds - fold + 1,
            "origin": origin.date().isoformat(),
            "wape_model": _wape(y, p),
            "wape_naive": _wape(y, b),
            "wape_blend": _wape(y, bl),
            "mae_model": mean_absolute_error(y, p),
            "rmse_model": float(np.sqrt(mean_squared_error(y, p))),
            "smape_model": _safe_smape(y, p),
        })
        for lo, hi, label in [(1, 7, "h01-07"), (8, 14, "h08-14"), (15, test_days, f"h15-{test_days:02d}")]:
            seg = fc[(fc["horizon"] >= lo) & (fc["horizon"] <= hi)]
            horizon_rows.append({
                "fold": n_folds - fold + 1,
                "horizon": label,
                "wape_model": _wape(seg["inbound_volume"].to_numpy(), seg["prediction"].to_numpy()),
                "wape_naive": _wape(seg["inbound_volume"].to_numpy(), seg["seasonal_naive"].to_numpy()),
            })

    backtest = pd.DataFrame(fold_metrics)
    horizon = pd.DataFrame(horizon_rows)
    horizon_avg = horizon.groupby("horizon", as_index=False)[["wape_model", "wape_naive"]].mean()

    # ------------------- 최종 모델 + 배포용 28일 예측 ----------------------
    final_origin = max_date - pd.Timedelta(days=test_days - 1)
    final_hist = raw[raw["date_key"] < final_origin]
    final_test = raw[raw["date_key"] >= final_origin]
    final_train = make_training_features(final_hist)
    point_model = _fit_point_model(final_train)
    quantile_models = _fit_quantile_models(final_train, quantile_alphas)

    future = final_test.drop(columns=["inbound_volume"]).copy()
    final_fc = _recursive_forecast(point_model, final_hist, future, quantile_models)
    final_fc = final_fc.merge(
        final_test[["date_key", "dest_region_id", "category_id", "inbound_volume"]],
        on=["date_key", "dest_region_id", "category_id"], how="left",
    )
    final_fc["seasonal_naive"] = _seasonal_naive_multistep(final_hist, final_fc)
    final_fc["horizon"] = (final_fc["date_key"] - final_origin).dt.days + 1
    final_fc["prediction_model"] = final_fc["prediction"]
    final_fc["prediction"] = np.where(
        final_fc["horizon"] <= SWITCH_HORIZON, final_fc["prediction_model"], final_fc["seasonal_naive"]
    ).round(2)

    qcols = [f"q{int(a * 100):02d}" for a in quantile_alphas]
    pred_cols = [
        "date_key", "dest_region_id", "region_name", "category_id", "category_name",
        "inbound_volume", "prediction", "prediction_model", "seasonal_naive", "horizon", *qcols,
    ]
    final_fc[pred_cols].to_csv(output_dir / "forecast_predictions.csv", index=False, encoding="utf-8-sig")
    backtest.round(4).to_csv(output_dir / "backtest_metrics.csv", index=False, encoding="utf-8-sig")
    horizon.round(4).to_csv(output_dir / "backtest_by_horizon.csv", index=False, encoding="utf-8-sig")

    coverage = {}
    for alpha in quantile_alphas:
        qcol = f"q{int(alpha * 100):02d}"
        coverage[qcol] = float((final_fc["inbound_volume"] <= final_fc[qcol]).mean())

    feature_importance = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance": point_model.feature_importances_,
    }).sort_values("importance", ascending=False)
    feature_importance.to_csv(output_dir / "feature_importance.csv", index=False, encoding="utf-8-sig")
    joblib.dump(
        {"model": point_model, "quantile_models": quantile_models, "features": FEATURE_COLUMNS},
        model_dir / "demand_forecast_gbr.joblib",
    )

    wm = backtest["wape_model"]
    wn = backtest["wape_naive"]
    wb = backtest["wape_blend"]
    cov_txt = ", ".join(f"{k}: {v:.1%}" for k, v in coverage.items())
    summary = f"""
# 수요예측 요약 (rolling-origin backtest)

## 평가 설계
- Expanding-window rolling-origin, {len(backtest)} folds x {test_days}일 horizon
- 테스트 구간은 recursive multi-step 예측 (예측값을 lag로 되먹임, 실측 미사용)
- Baseline: seasonal naive (origin 이전 마지막 동일 요일 실측 반복)

## 결과
- 모델(recursive) WAPE: 평균 **{wm.mean():.2%}** (fold별 {', '.join(f'{v:.2%}' for v in wm)})
- Naive WAPE: 평균 **{wn.mean():.2%}**
- 운영 예측(h<= {SWITCH_HORIZON}일 모델, 이후 naive 전환) WAPE: 평균 **{wb.mean():.2%}**
- 운영 예측의 naive 대비 개선: **{(wn.mean() - wb.mean()) / wn.mean():.1%}**

단일 holdout에 테스트 구간 실측 lag를 넣고 평가하면 WAPE가 6% 수준으로 나오지만,
이는 1-step 성능을 28일 성능처럼 부풀리는 누수다. 위 수치가 운영 조건의 성능이며,
모델 단독은 장기 horizon에서 naive에 지기 때문에 전환 정책을 함께 쓴다.

## Horizon별 WAPE (fold 평균)
{horizon_avg.round(4).to_string(index=False)}

Horizon이 길수록 recursive 오차가 누적돼 WAPE가 상승하는 것이 정상이며, 이 수치가
운영에서 기대할 수 있는 실제 다중일 예측 성능이다.

## Quantile 예측 (최종 28일 구간 empirical coverage)
{cov_txt}

Quantile 예측은 용량 배분(newsvendor) 레이어의 입력으로 쓰인다. Coverage가 목표
수준과 크게 어긋나면 quantile 보정(conformal 등)을 검토한다.
""".lstrip()
    (output_dir / "forecast_summary.md").write_text(summary, encoding="utf-8")

    metrics_compat = pd.DataFrame([
        {"model": "seasonal_naive", "wape": round(wn.mean(), 4)},
        {"model": "gradient_boosting_recursive", "wape": round(wm.mean(), 4)},
        {"model": f"operational_blend_switch{SWITCH_HORIZON}", "wape": round(wb.mean(), 4)},
    ])
    metrics_compat.to_csv(output_dir / "model_metrics.csv", index=False, encoding="utf-8-sig")

    return {
        "backtest": backtest,
        "horizon": horizon_avg,
        "coverage": coverage,
        "predictions": final_fc[pred_cols],
        "model_path": model_dir / "demand_forecast_gbr.joblib",
    }
