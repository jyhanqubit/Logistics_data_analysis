from __future__ import annotations

import pandas as pd


def compute_oms_kpi(orders_df: pd.DataFrame, order_events_df: pd.DataFrame) -> pd.DataFrame:
    if orders_df.empty:
        return pd.DataFrame(columns=["kpi", "value"])

    received = order_events_df[order_events_df["event_type"] == "ORDER_RECEIVED"][["order_id", "event_ts"]].rename(columns={"event_ts": "received_ts"})
    released = order_events_df[order_events_df["event_type"] == "RELEASED_TO_WMS"][["order_id", "event_ts"]].rename(columns={"event_ts": "released_ts"})
    cancelled = set(order_events_df.loc[order_events_df["event_type"] == "CANCELLED", "order_id"])

    lead = received.merge(released, on="order_id", how="inner")
    lead_hours = ((pd.to_datetime(lead["released_ts"]) - pd.to_datetime(lead["received_ts"])) / pd.Timedelta(hours=1)).mean()

    by_day = orders_df.groupby("order_date", as_index=False).size().rename(columns={"size": "cnt"})
    peak_ratio = by_day["cnt"].max() / by_day["cnt"].sum() if len(by_day) else 0

    return pd.DataFrame(
        {
            "kpi": [
                "order_count",
                "order_to_release_lead_time",
                "cancellation_rate",
                "backorder_rate",
                "peak_order_ratio",
            ],
            "value": [
                float(len(orders_df)),
                float(0 if pd.isna(lead_hours) else lead_hours),
                float(len(cancelled) / max(1, len(orders_df))),
                float(0.0),
                float(peak_ratio),
            ],
        }
    )


def compute_wms_kpi(inventory_df: pd.DataFrame, pick_pack_df: pd.DataFrame, stockout_risk_df: pd.DataFrame) -> pd.DataFrame:
    if inventory_df.empty:
        return pd.DataFrame(columns=["kpi", "value"])

    turnover = (inventory_df["daily_demand"].sum() * 30) / max(1.0, inventory_df["on_hand"].mean())
    productivity = len(pick_pack_df) / max(1.0, pick_pack_df["pick_seconds"].sum() / 3600)

    return pd.DataFrame(
        {
            "kpi": [
                "inventory_turnover",
                "stockout_risk_score",
                "picking_productivity",
                "warehouse_utilization",
                "pick_pack_cycle_time",
            ],
            "value": [
                float(turnover),
                float(stockout_risk_df["stockout_risk_score"].mean() if not stockout_risk_df.empty else 0),
                float(productivity),
                float(inventory_df["warehouse_utilization"].mean()),
                float(pick_pack_df["cycle_time_seconds"].mean() if not pick_pack_df.empty else 0),
            ],
        }
    )


def compute_tms_kpi(shipments_df: pd.DataFrame, delivery_df: pd.DataFrame, sla_df: pd.DataFrame) -> pd.DataFrame:
    if shipments_df.empty:
        return pd.DataFrame(columns=["kpi", "value"])

    on_time = sla_df["is_on_time"].mean() if not sla_df.empty else 0
    vehicle_utilization = min(1.0, len(shipments_df) / 15000)

    return pd.DataFrame(
        {
            "kpi": [
                "on_time_delivery_rate",
                "vehicle_utilization",
                "route_distance",
                "cost_per_delivery",
                "late_delivery_risk_score",
            ],
            "value": [
                float(on_time),
                float(vehicle_utilization),
                float(delivery_df["actual_distance_km"].sum() if not delivery_df.empty else 0),
                float(delivery_df["actual_cost"].mean() if not delivery_df.empty else 0),
                float(1 - on_time),
            ],
        }
    )
