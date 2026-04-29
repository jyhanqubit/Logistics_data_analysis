from __future__ import annotations

import numpy as np
import pandas as pd


def generate_shipments(orders_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    if orders_df.empty:
        return pd.DataFrame(columns=["shipment_id", "order_id", "region_id", "planned_distance_km", "planned_cost"])

    rng = np.random.default_rng(seed)
    ship = orders_df[["order_id", "region_id", "promised_hours"]].copy()
    ship["shipment_id"] = [f"S{i:09d}" for i in range(1, len(ship) + 1)]
    ship["planned_distance_km"] = rng.uniform(2.5, 28.0, len(ship)).round(2)
    ship["planned_cost"] = (3200 + ship["planned_distance_km"] * rng.uniform(90, 150, len(ship))).round(0)
    return ship[["shipment_id", "order_id", "region_id", "promised_hours", "planned_distance_km", "planned_cost"]]


def generate_delivery_events(shipments_df: pd.DataFrame, order_events_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    if shipments_df.empty:
        return pd.DataFrame(columns=["shipment_id", "pickup_ts", "delivered_ts", "actual_distance_km", "actual_cost"])

    rng = np.random.default_rng(seed)
    release = (
        order_events_df[order_events_df["event_type"] == "RELEASED_TO_WMS"][["order_id", "event_ts"]]
        .rename(columns={"event_ts": "released_ts"})
        .copy()
    )
    merged = shipments_df.merge(release, on="order_id", how="left")
    base_ts = pd.to_datetime(merged["released_ts"]).fillna(pd.Timestamp("2025-01-01"))

    pickup = base_ts + pd.to_timedelta(rng.integers(20, 240, size=len(merged)), unit="m")
    transit_hours = rng.uniform(4, 36, size=len(merged))
    delivered = pickup + pd.to_timedelta(transit_hours, unit="h")

    out = pd.DataFrame(
        {
            "shipment_id": merged["shipment_id"],
            "pickup_ts": pickup,
            "delivered_ts": delivered,
            "actual_distance_km": (merged["planned_distance_km"] * rng.uniform(0.9, 1.25, len(merged))).round(2),
            "actual_cost": (merged["planned_cost"] * rng.uniform(0.92, 1.22, len(merged))).round(0),
        }
    )
    return out


def calculate_delivery_sla(shipments_df: pd.DataFrame, delivery_events_df: pd.DataFrame) -> pd.DataFrame:
    if shipments_df.empty or delivery_events_df.empty:
        return pd.DataFrame(columns=["shipment_id", "delivered_in_hours", "promised_hours", "is_on_time"])

    merged = shipments_df[["shipment_id", "promised_hours"]].merge(delivery_events_df, on="shipment_id", how="inner")
    delivered_in_hours = (pd.to_datetime(merged["delivered_ts"]) - pd.to_datetime(merged["pickup_ts"])) / pd.Timedelta(hours=1)
    merged["delivered_in_hours"] = delivered_in_hours
    merged["is_on_time"] = merged["delivered_in_hours"] <= merged["promised_hours"]
    return merged[["shipment_id", "delivered_in_hours", "promised_hours", "is_on_time"]]
