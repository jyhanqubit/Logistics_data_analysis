from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parcelflow.ops_simulation import run_ops_simulation


def test_run_ops_simulation_outputs(tmp_path: Path) -> None:
    processed = tmp_path / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {"date_key": "2025-01-01", "dest_region_id": 1, "category_id": 1, "inbound_volume": 50},
            {"date_key": "2025-01-02", "dest_region_id": 2, "category_id": 2, "inbound_volume": 60},
        ]
    ).to_csv(processed / "fact_daily_demand.csv", index=False)

    out = run_ops_simulation(processed, tmp_path / "outputs", seed=42)
    assert (tmp_path / "outputs" / "orders.csv").exists()
    assert set(out.keys()) == {
        "orders",
        "order_lines",
        "order_events",
        "inventory_snapshot",
        "pick_pack_events",
        "shipments",
        "delivery_events",
        "oms_kpi",
        "wms_kpi",
        "tms_kpi",
    }

    oms_kpi = pd.read_csv(tmp_path / "outputs" / "oms_kpi.csv")
    assert "order_count" in set(oms_kpi["kpi"])
