from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def _smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = (np.abs(y_true) + np.abs(y_pred))
    denom = np.where(denom == 0, 1, denom)
    return float(np.mean(2 * np.abs(y_true - y_pred) / denom))


def _wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sum(np.abs(y_true - y_pred)) / max(1, np.sum(np.abs(y_true))))


def run_regression_analysis(feature_df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = feature_df.sort_values("date_key").copy()
    y = df["inbound_volume"].astype(float)
    exclude = {"date_key", "inbound_volume"}
    X = df[[c for c in df.columns if c not in exclude and np.issubdtype(df[c].dtype, np.number)]].copy()

    cut = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:cut], X.iloc[cut:]
    y_train, y_test = y.iloc[:cut], y.iloc[cut:]

    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "Lasso": Lasso(alpha=0.001),
        "ElasticNet": ElasticNet(alpha=0.001, l1_ratio=0.5),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=120, random_state=42),
        "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
        "HistGradientBoostingRegressor": HistGradientBoostingRegressor(random_state=42),
    }

    metric_rows: list[dict] = []
    pred_rows: list[pd.DataFrame] = []
    fi_rows: list[dict] = []

    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        peak_mask = X_test.get("is_peak_season", pd.Series([0] * len(X_test), index=X_test.index)) > 0
        peak_wape = _wape(y_test[peak_mask], pred[peak_mask]) if peak_mask.any() else np.nan

        metric_rows.append(
            {
                "model": name,
                "MAE": mean_absolute_error(y_test, pred),
                "RMSE": mean_squared_error(y_test, pred) ** 0.5,
                "R2": r2_score(y_test, pred),
                "MAPE": float(np.mean(np.abs((y_test - pred) / np.maximum(1, y_test)))),
                "sMAPE": _smape(y_test.to_numpy(), pred),
                "WAPE": _wape(y_test.to_numpy(), pred),
                "Peak-season WAPE": peak_wape,
            }
        )

        p = pd.DataFrame({"date_key": df.iloc[cut:]["date_key"].values, "y_true": y_test.values, "y_pred": pred, "model": name})
        pred_rows.append(p)

        if hasattr(model, "feature_importances_"):
            imp = model.feature_importances_
        elif hasattr(model, "coef_"):
            imp = np.abs(np.ravel(model.coef_))
        else:
            imp = np.zeros(X_train.shape[1])
        top_idx = np.argsort(imp)[::-1][:20]
        for idx in top_idx:
            fi_rows.append({"model": name, "feature": X_train.columns[idx], "importance": float(imp[idx])})

    mdf = pd.DataFrame(metric_rows).sort_values("WAPE")
    pdf = pd.concat(pred_rows, ignore_index=True)
    fidf = pd.DataFrame(fi_rows)

    metrics_path = out_dir / "regression_model_metrics.csv"
    pred_path = out_dir / "regression_predictions.csv"
    fi_path = out_dir / "regression_feature_importance.csv"
    summary_path = out_dir / "regression_summary.md"

    mdf.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    pdf.to_csv(pred_path, index=False, encoding="utf-8-sig")
    fidf.to_csv(fi_path, index=False, encoding="utf-8-sig")
    summary_path.write_text("# Regression Summary\n\n지역·상품군 수요 회귀모델 비교 결과입니다.\n", encoding="utf-8")

    return {"metrics": metrics_path, "predictions": pred_path, "feature_importance": fi_path, "summary": summary_path}
