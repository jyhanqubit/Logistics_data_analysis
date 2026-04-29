from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


EXPECTED_CASE_FILES = [
    "analysis_cases/README.md",
    "analysis_cases/01_oms_order_flow_analysis.md",
    "analysis_cases/02_oms_peak_order_risk.md",
    "analysis_cases/03_wms_inventory_risk.md",
    "analysis_cases/04_wms_picking_workload.md",
    "analysis_cases/05_tms_delivery_sla.md",
    "analysis_cases/06_tms_route_optimization.md",
    "analysis_cases/07_forecasting_demand_by_region_category.md",
    "analysis_cases/08_recommendation_locker_site.md",
    "analysis_cases/09_vector_db_copilot.md",
    "analysis_cases/sql/01_oms_order_flow.sql",
    "analysis_cases/sql/03_wms_inventory_risk.sql",
    "analysis_cases/sql/05_tms_delivery_sla.sql",
    "analysis_cases/sql/07_forecasting_dataset.sql",
]


def test_analysis_casebook_files_exist() -> None:
    missing = [p for p in EXPECTED_CASE_FILES if not (ROOT / p).exists()]
    assert not missing, f"Missing casebook files: {missing}"
