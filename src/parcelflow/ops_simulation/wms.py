from __future__ import annotations

import numpy as np
import pandas as pd


def generate_inventory_snapshot(order_lines_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    if order_lines_df.empty:
        return pd.DataFrame(columns=["sku_id", "on_hand", "daily_demand", "warehouse_utilization"])

    rng = np.random.default_rng(seed)
    demand = order_lines_df.groupby("sku_id", as_index=False)["line_qty"].sum().rename(columns={"line_qty": "daily_demand"})
    demand["on_hand"] = (demand["daily_demand"] * rng.uniform(3, 12, size=len(demand))).round().astype(int)
    demand["warehouse_utilization"] = rng.uniform(0.55, 0.93, size=len(demand)).round(4)
    return demand[["sku_id", "on_hand", "daily_demand", "warehouse_utilization"]]


def generate_pick_pack_events(order_lines_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    if order_lines_df.empty:
        return pd.DataFrame(columns=["order_id", "line_no", "pick_seconds", "pack_seconds", "cycle_time_seconds"])

    rng = np.random.default_rng(seed)
    events = order_lines_df[["order_id", "line_no", "line_qty"]].copy()
    events["pick_seconds"] = (events["line_qty"] * rng.uniform(18, 45, len(events))).round().astype(int)
    events["pack_seconds"] = (events["line_qty"] * rng.uniform(12, 30, len(events))).round().astype(int)
    events["cycle_time_seconds"] = events["pick_seconds"] + events["pack_seconds"]
    return events[["order_id", "line_no", "pick_seconds", "pack_seconds", "cycle_time_seconds"]]


def calculate_stockout_risk(inventory_snapshot_df: pd.DataFrame) -> pd.DataFrame:
    if inventory_snapshot_df.empty:
        return pd.DataFrame(columns=["sku_id", "stockout_risk_score"])

    df = inventory_snapshot_df.copy()
    coverage_days = df["on_hand"] / df["daily_demand"].replace(0, 1)
    score = (1 / coverage_days).clip(0, 1)
    return pd.DataFrame({"sku_id": df["sku_id"], "stockout_risk_score": score.round(4)})
