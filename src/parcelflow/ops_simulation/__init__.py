from __future__ import annotations

from pathlib import Path

import pandas as pd

from .kpi import compute_oms_kpi, compute_tms_kpi, compute_wms_kpi
from .oms import generate_order_lines, generate_orders_from_demand, generate_order_status_events
from .tms import calculate_delivery_sla, generate_delivery_events, generate_shipments
from .wms import calculate_stockout_risk, generate_inventory_snapshot, generate_pick_pack_events


def run_ops_simulation(processed_dir: Path, output_dir: Path, seed: int = 42) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    demand = pd.read_csv(processed_dir / "fact_daily_demand.csv")

    orders = generate_orders_from_demand(demand, seed=seed)
    order_lines = generate_order_lines(orders, seed=seed)
    order_events = generate_order_status_events(orders, seed=seed)

    inventory = generate_inventory_snapshot(order_lines, seed=seed)
    pick_pack = generate_pick_pack_events(order_lines, seed=seed)
    stockout = calculate_stockout_risk(inventory)

    shipments = generate_shipments(orders, seed=seed)
    delivery = generate_delivery_events(shipments, order_events, seed=seed)
    sla = calculate_delivery_sla(shipments, delivery)

    oms_kpi = compute_oms_kpi(orders, order_events)
    wms_kpi = compute_wms_kpi(inventory, pick_pack, stockout)
    tms_kpi = compute_tms_kpi(shipments, delivery, sla)

    files = {
        "orders": output_dir / "orders.csv",
        "order_lines": output_dir / "order_lines.csv",
        "inventory_snapshot": output_dir / "inventory_snapshot.csv",
        "pick_pack_events": output_dir / "pick_pack_events.csv",
        "shipments": output_dir / "shipments.csv",
        "delivery_events": output_dir / "delivery_events.csv",
        "oms_kpi": output_dir / "oms_kpi.csv",
        "wms_kpi": output_dir / "wms_kpi.csv",
        "tms_kpi": output_dir / "tms_kpi.csv",
    }

    orders.to_csv(files["orders"], index=False, encoding="utf-8-sig")
    order_lines.to_csv(files["order_lines"], index=False, encoding="utf-8-sig")
    inventory.to_csv(files["inventory_snapshot"], index=False, encoding="utf-8-sig")
    pick_pack.to_csv(files["pick_pack_events"], index=False, encoding="utf-8-sig")
    shipments.to_csv(files["shipments"], index=False, encoding="utf-8-sig")
    delivery.to_csv(files["delivery_events"], index=False, encoding="utf-8-sig")
    oms_kpi.to_csv(files["oms_kpi"], index=False, encoding="utf-8-sig")
    wms_kpi.to_csv(files["wms_kpi"], index=False, encoding="utf-8-sig")
    tms_kpi.to_csv(files["tms_kpi"], index=False, encoding="utf-8-sig")

    return files


__all__ = [
    "run_ops_simulation",
    "generate_orders_from_demand",
    "generate_order_lines",
    "generate_order_status_events",
    "generate_inventory_snapshot",
    "generate_pick_pack_events",
    "calculate_stockout_risk",
    "generate_shipments",
    "generate_delivery_events",
    "calculate_delivery_sla",
]
