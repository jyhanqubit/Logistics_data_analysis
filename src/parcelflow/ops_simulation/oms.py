from __future__ import annotations

import numpy as np
import pandas as pd


def generate_orders_from_demand(demand_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Create OMS order headers from 공개 물동량 기반 수요 데이터 (simulation layer)."""
    if demand_df.empty:
        return pd.DataFrame(columns=["order_id", "order_date", "region_id", "category_id", "qty", "promised_hours"])

    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    order_id = 1
    for _, row in demand_df.iterrows():
        inbound = int(max(0, row.get("inbound_volume", 0)))
        order_cnt = min(30, max(1, inbound // 40))
        for _ in range(order_cnt):
            qty = int(max(1, rng.poisson(lam=2)))
            rows.append(
                {
                    "order_id": f"O{order_id:09d}",
                    "order_date": row["date_key"],
                    "region_id": int(row["dest_region_id"]),
                    "category_id": int(row["category_id"]),
                    "qty": qty,
                    "promised_hours": int(rng.choice([12, 24, 36], p=[0.25, 0.65, 0.10])),
                }
            )
            order_id += 1

    return pd.DataFrame(rows)


def generate_order_lines(orders_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    if orders_df.empty:
        return pd.DataFrame(columns=["order_id", "line_no", "sku_id", "line_qty"])

    rng = np.random.default_rng(seed)
    lines: list[dict] = []
    for _, row in orders_df.iterrows():
        line_count = int(rng.integers(1, 4))
        qty_remaining = int(row["qty"])
        for line_no in range(1, line_count + 1):
            if line_no == line_count:
                line_qty = max(1, qty_remaining)
            else:
                line_qty = int(max(1, rng.integers(1, max(2, qty_remaining))))
                qty_remaining -= line_qty
            lines.append(
                {
                    "order_id": row["order_id"],
                    "line_no": line_no,
                    "sku_id": f"SKU-{int(row['category_id']):02d}-{int(rng.integers(1, 200)):04d}",
                    "line_qty": int(line_qty),
                }
            )
    return pd.DataFrame(lines)


def generate_order_status_events(orders_df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Generate OMS lifecycle events (simulation) from order headers."""
    if orders_df.empty:
        return pd.DataFrame(columns=["order_id", "event_type", "event_ts"])

    rng = np.random.default_rng(seed)
    events: list[dict] = []
    base = pd.to_datetime(orders_df["order_date"])

    for idx, row in orders_df.reset_index(drop=True).iterrows():
        t0 = base.iloc[idx] + pd.Timedelta(minutes=int(rng.integers(0, 1440)))
        t_release = t0 + pd.Timedelta(minutes=int(rng.integers(20, 360)))
        is_cancel = rng.random() < 0.03
        is_return = rng.random() < 0.02

        events.extend(
            [
                {"order_id": row["order_id"], "event_type": "ORDER_RECEIVED", "event_ts": t0},
                {"order_id": row["order_id"], "event_type": "RELEASED_TO_WMS", "event_ts": t_release},
            ]
        )

        if is_cancel:
            events.append(
                {
                    "order_id": row["order_id"],
                    "event_type": "CANCELLED",
                    "event_ts": t0 + pd.Timedelta(minutes=int(rng.integers(5, 180))),
                }
            )

        if is_return and not is_cancel:
            events.append(
                {
                    "order_id": row["order_id"],
                    "event_type": "RETURN_REQUESTED",
                    "event_ts": t_release + pd.Timedelta(hours=int(rng.integers(24, 168))),
                }
            )

    return pd.DataFrame(events).sort_values(["order_id", "event_ts"]).reset_index(drop=True)
