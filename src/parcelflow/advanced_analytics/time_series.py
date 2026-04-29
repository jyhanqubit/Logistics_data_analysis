from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
except Exception:  # optional dependency fallback
    ARIMA = None
    seasonal_decompose = None


def run_time_series_analysis(feature_df: pd.DataFrame, out_dir: Path, max_lag: int = 28) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = feature_df.copy().sort_values("date_key")

    ts = (
        df.groupby("date_key", as_index=False)["inbound_volume"].sum().rename(columns={"inbound_volume": "observed"})
    )
    ts["date_key"] = pd.to_datetime(ts["date_key"])
    ts["trend"] = ts["observed"].rolling(28, min_periods=2).mean()
    dow_mean = ts.groupby(ts["date_key"].dt.dayofweek)["observed"].transform("mean")
    ts["seasonal"] = dow_mean
    ts["residual"] = ts["observed"] - ts["trend"].fillna(0) - ts["seasonal"].fillna(0)
    if seasonal_decompose is not None:
        try:
            dec = seasonal_decompose(ts.set_index("date_key")["observed"], model="additive", period=7, extrapolate_trend="freq")
            ts["trend"] = dec.trend.values
            ts["seasonal"] = dec.seasonal.values
            ts["residual"] = dec.resid.values
        except Exception:
            pass

    rows = []
    s = ts["observed"].fillna(0)
    for lag in range(1, max_lag + 1):
        rows.append({"series_id": "all", "region_name": "all", "product_category": "all", "function_type": "ACF", "lag": lag, "correlation": s.autocorr(lag)})
        rows.append({"series_id": "all", "region_name": "all", "product_category": "all", "function_type": "PACF", "lag": lag, "correlation": s.diff().autocorr(lag)})

    rolling = ts[["date_key", "observed"]].copy()
    rolling["rolling_mean_7"] = rolling["observed"].rolling(7, min_periods=2).mean()
    rolling["rolling_std_7"] = rolling["observed"].rolling(7, min_periods=2).std().fillna(0)

    ccf = []
    reg_daily = df.groupby(["date_key", "dest_region_id"], as_index=False)["inbound_volume"].sum()
    pivot = reg_daily.pivot(index="date_key", columns="dest_region_id", values="inbound_volume").fillna(0)
    cols = list(pivot.columns[:3])
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, b = pivot[cols[i]], pivot[cols[j]]
            corr = a.corr(b)
            ccf.append({"series_a": str(cols[i]), "series_b": str(cols[j]), "lag": 0, "correlation": corr, "abs_correlation": abs(corr), "interpretation": "동행상관"})

    if ARIMA is not None:
        try:
            arima = ARIMA(ts["observed"].astype(float), order=(1, 1, 1)).fit()
            ts["arima_fitted"] = arima.predict(start=1, end=len(ts))
        except Exception:
            ts["arima_fitted"] = np.nan
    else:
        ts["arima_fitted"] = np.nan

    decomp_path = out_dir / "decomposition.csv"
    acf_path = out_dir / "acf_pacf.csv"
    ccf_path = out_dir / "cross_correlation.csv"
    roll_path = out_dir / "rolling_statistics.csv"
    summary_path = out_dir / "time_series_summary.md"

    ts.to_csv(decomp_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(rows).to_csv(acf_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(ccf).to_csv(ccf_path, index=False, encoding="utf-8-sig")
    rolling.to_csv(roll_path, index=False, encoding="utf-8-sig")
    summary_path.write_text("# Time Series Summary\n\n추세/계절성/자기상관 분석 결과입니다.\n", encoding="utf-8")

    return {"decomposition": decomp_path, "acf_pacf": acf_path, "cross_correlation": ccf_path, "rolling": roll_path, "summary": summary_path}
