from __future__ import annotations

import numpy as np
import pandas as pd


def build_advanced_features(demand_df: pd.DataFrame) -> pd.DataFrame:
    df = demand_df.copy()
    df["date_key"] = pd.to_datetime(df["date_key"], errors="coerce")
    df = df.dropna(subset=["date_key"]).sort_values(["dest_region_id", "category_id", "date_key"])
    g = df.groupby(["dest_region_id", "category_id"], group_keys=False)

    df["year"] = df["date_key"].dt.year
    df["month"] = df["date_key"].dt.month
    df["day"] = df["date_key"].dt.day
    df["day_of_week"] = df["date_key"].dt.dayofweek
    df["week_of_year"] = df["date_key"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["is_month_start"] = df["date_key"].dt.is_month_start.astype(int)
    df["is_month_end"] = df["date_key"].dt.is_month_end.astype(int)
    df["is_peak_season"] = df["month"].isin([11, 12]).astype(int)

    region_stats = df.groupby("dest_region_id")["inbound_volume"]
    df["region_avg_volume"] = df["dest_region_id"].map(region_stats.mean())
    df["region_median_volume"] = df["dest_region_id"].map(region_stats.median())
    df["region_std_volume"] = df["dest_region_id"].map(region_stats.std().fillna(0))
    df["region_cv"] = df["region_std_volume"] / df["region_avg_volume"].replace(0, np.nan)

    cat_stats = df.groupby("category_id")["inbound_volume"]
    df["category_avg_volume"] = df["category_id"].map(cat_stats.mean())
    df["category_std_volume"] = df["category_id"].map(cat_stats.std().fillna(0))

    rc_stats = df.groupby(["dest_region_id", "category_id"])["inbound_volume"]
    rc_mean = rc_stats.transform("mean")
    rc_std = rc_stats.transform("std").fillna(0)
    df["region_category_avg_volume"] = rc_mean
    df["region_category_cv"] = rc_std / rc_mean.replace(0, np.nan)

    for lag in [1, 7, 14, 28]:
        df[f"lag_{lag}"] = g["inbound_volume"].shift(lag)

    for w in [7, 14, 28]:
        roll = g["inbound_volume"].rolling(w, min_periods=2)
        df[f"rolling_mean_{w}"] = roll.mean().reset_index(level=[0, 1], drop=True)
    for w in [7, 14]:
        roll = g["inbound_volume"].rolling(w, min_periods=2)
        df[f"rolling_std_{w}"] = roll.std().reset_index(level=[0, 1], drop=True)
    roll28 = g["inbound_volume"].rolling(28, min_periods=2)
    df["rolling_max_28"] = roll28.max().reset_index(level=[0, 1], drop=True)
    df["rolling_min_28"] = roll28.min().reset_index(level=[0, 1], drop=True)

    df["expanding_mean"] = g["inbound_volume"].expanding().mean().reset_index(level=[0, 1], drop=True)
    df["ewma_7"] = g["inbound_volume"].transform(lambda s: s.ewm(span=7, adjust=False).mean())
    df["ewma_14"] = g["inbound_volume"].transform(lambda s: s.ewm(span=14, adjust=False).mean())

    df["peak_ratio_30d"] = df["rolling_max_28"] / df["rolling_mean_28"].replace(0, np.nan)
    df["above_rolling_mean_flag"] = (df["inbound_volume"] > df["rolling_mean_28"]).astype(int)
    df["demand_spike_score"] = (df["inbound_volume"] - df["rolling_mean_28"]).clip(lower=0) / df["rolling_std_14"].replace(0, 1)

    cat_share = (
        df.groupby(["dest_region_id", "category_id"])["inbound_volume"].sum()
        / df.groupby("dest_region_id")["inbound_volume"].sum()
    ).reset_index(name="share")
    entropy = cat_share.groupby("dest_region_id")["share"].apply(lambda s: -np.sum(np.where(s > 0, s * np.log(s), 0)))
    top_share = cat_share.groupby("dest_region_id")["share"].max()
    df["category_entropy_by_region"] = df["dest_region_id"].map(entropy)
    df["top_category_share_by_region"] = df["dest_region_id"].map(top_share)

    lane_rank = (
        df.groupby(["dest_region_id", "category_id"])["inbound_volume"].transform("mean").rank(pct=True)
    )
    df["od_lane_volume_rank"] = lane_rank
    df["nearest_hub_distance_km"] = 5 + (df["dest_region_id"] % 5) * 1.5

    return df.fillna(0)
