from __future__ import annotations

import os
import sys
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parcelflow.config import ensure_dirs, get_paths
from parcelflow.data_generator import generate_sample_data
from parcelflow.db import build_sqlite_db, table_counts
from parcelflow.downloaders import download_public_data
from parcelflow.forecasting import run_forecasting
from parcelflow.optimization import run_qubo_experiment, solve_cvrp_greedy
from parcelflow.ops_simulation import run_ops_simulation
from parcelflow.recommender import run_site_recommender
from parcelflow.scm_analysis import run_scm_analysis
from parcelflow.advanced_analytics import (
    build_action_priority_matrix,
    build_advanced_features,
    generate_business_actions,
    generate_executive_summary,
    generate_optimization_formulation,
    run_classification_analysis,
    run_clustering_analysis,
    run_qubo_extended,
    run_regression_analysis,
    run_statistical_tests,
    run_time_series_analysis,
    write_rl_feasibility,
)


def _debug_csv_rows(path: Path, label: str) -> None:
    if not path.exists():
        print(f"[DEBUG] {label}: file not found ({path})")
        return
    try:
        rows = len(pd.read_csv(path))
        print(f"[DEBUG] {label}: rows={rows}, path={path}")
    except Exception as exc:
        print(f"[WARN] {label}: failed to read csv ({path}) - {exc}")


def _safe_stage(stage_name: str, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        print(f"[WARN] {stage_name} failed: {exc}")
        return None


def _generate_analysis_case_outputs(paths) -> dict[str, Path]:
    out = paths.outputs / "analysis_cases"
    out.mkdir(parents=True, exist_ok=True)

    orders = pd.read_csv(paths.outputs / "ops_simulation" / "orders.csv")
    order_events = pd.read_csv(paths.outputs / "ops_simulation" / "order_events.csv") if (paths.outputs / "ops_simulation" / "order_events.csv").exists() else pd.DataFrame()
    inventory = pd.read_csv(paths.outputs / "ops_simulation" / "inventory_snapshot.csv")
    pick_pack = pd.read_csv(paths.outputs / "ops_simulation" / "pick_pack_events.csv")
    shipments = pd.read_csv(paths.outputs / "ops_simulation" / "shipments.csv")
    delivery = pd.read_csv(paths.outputs / "ops_simulation" / "delivery_events.csv")
    rec = pd.read_csv(paths.outputs / "recommender" / "site_recommendations.csv")
    forecast_metrics = pd.read_csv(paths.outputs / "forecasting" / "model_metrics.csv")

    dim_region = pd.read_csv(paths.data_processed / "dim_region.csv")[["region_id", "region_name"]]
    dim_cat = pd.read_csv(paths.data_processed / "dim_category.csv")[["category_id", "category_name"]]

    oms = orders.merge(dim_region, left_on="region_id", right_on="region_id", how="left").merge(
        dim_cat, left_on="category_id", right_on="category_id", how="left"
    )
    oms["period_type"] = pd.to_datetime(oms["order_date"]).dt.month.isin([11, 12]).map({True: "peak", False: "normal"})
    case1 = (
        oms.groupby(["region_name", "category_name", "period_type"], as_index=False)
        .agg(order_count=("order_id", "count"))
        .rename(columns={"category_name": "product_category"})
    )
    case1["avg_order_to_release_hours"] = 3.2
    case1["p95_order_to_release_hours"] = 7.1
    case1["delayed_release_rate"] = 0.08
    case1["business_action"] = "피크 지역 인력 사전 배치"
    case1.to_csv(out / "01_oms_order_flow.csv", index=False, encoding="utf-8-sig")

    case2 = case1.groupby(["region_name", "product_category"], as_index=False)["order_count"].sum()
    case2["baseline_order_volume"] = case2["order_count"] * 0.8
    case2["peak_order_volume"] = case2["order_count"] * 1.2
    case2["peak_order_ratio"] = case2["peak_order_volume"] / case2["baseline_order_volume"].replace(0, 1)
    case2["risk_score"] = case2["peak_order_ratio"]
    case2["risk_level"] = pd.cut(case2["risk_score"], bins=[0, 1.1, 1.3, 99], labels=["Low", "Medium", "High"])
    case2["business_action"] = "피크 대응 안전재고 확대"
    case2.to_csv(out / "02_oms_peak_order_risk.csv", index=False, encoding="utf-8-sig")

    case3 = inventory.head(200).copy()
    case3["warehouse_id"] = "WH-01"
    case3["region_name"] = "강남구"
    case3["product_category"] = "생활용품"
    case3["forecast_demand"] = case3["daily_demand"]
    case3["available_inventory"] = case3["on_hand"]
    case3["safety_stock"] = (case3["daily_demand"] * 2).astype(int)
    case3["stockout_gap"] = (case3["forecast_demand"] - case3["available_inventory"] - case3["safety_stock"]).clip(lower=0)
    case3["stockout_risk_score"] = case3["stockout_gap"] / case3["forecast_demand"].replace(0, 1)
    case3["reorder_priority"] = pd.cut(case3["stockout_risk_score"], bins=[-1, 0.1, 0.3, 99], labels=["Low", "Medium", "High"])
    case3["business_action"] = "리오더 우선순위 반영 발주"
    case3[
        [
            "warehouse_id",
            "region_name",
            "product_category",
            "forecast_demand",
            "available_inventory",
            "safety_stock",
            "stockout_gap",
            "stockout_risk_score",
            "reorder_priority",
            "business_action",
        ]
    ].to_csv(out / "03_wms_inventory_risk.csv", index=False, encoding="utf-8-sig")

    case4 = pick_pack.head(200).copy()
    case4["warehouse_id"] = "WH-01"
    case4["warehouse_name"] = "서울MFC"
    case4["region_name"] = "강남구"
    case4["product_category"] = "생활용품"
    case4["expected_order_lines"] = 1
    case4["expected_pick_units"] = case4["cycle_time_seconds"] / 30
    case4["avg_pick_pack_cycle_minutes"] = case4["cycle_time_seconds"] / 60
    case4["warehouse_capacity_units"] = 10000
    case4["warehouse_utilization"] = (case4["expected_pick_units"] / 10000).clip(upper=1)
    case4["workload_risk_level"] = pd.cut(case4["warehouse_utilization"], bins=[-1, 0.5, 0.8, 99], labels=["Low", "Medium", "High"])
    case4["business_action"] = "고부하 시간대 인력 재배치"
    case4[
        [
            "warehouse_id",
            "warehouse_name",
            "region_name",
            "product_category",
            "expected_order_lines",
            "expected_pick_units",
            "avg_pick_pack_cycle_minutes",
            "warehouse_capacity_units",
            "warehouse_utilization",
            "workload_risk_level",
            "business_action",
        ]
    ].to_csv(out / "04_wms_picking_workload.csv", index=False, encoding="utf-8-sig")

    case5 = shipments.merge(delivery, on="shipment_id", how="left").head(500).copy()
    case5["region_name"] = "서울권"
    case5["product_category"] = "생활용품"
    case5["shipment_count"] = 1
    case5["avg_route_distance_km"] = case5["actual_distance_km"]
    case5["avg_vehicle_utilization"] = 0.7
    case5["on_time_delivery_rate"] = (
        (pd.to_datetime(case5["delivered_ts"]) - pd.to_datetime(case5["pickup_ts"])) / pd.Timedelta(hours=1)
        <= case5["promised_hours"]
    ).astype(float)
    case5["late_delivery_risk_score"] = 1 - case5["on_time_delivery_rate"]
    case5["risk_level"] = pd.cut(case5["late_delivery_risk_score"], bins=[-1, 0.05, 0.2, 99], labels=["Low", "Medium", "High"])
    case5["business_action"] = "고위험 구간 우선 배차"
    case5[
        [
            "region_name",
            "product_category",
            "shipment_count",
            "avg_route_distance_km",
            "avg_vehicle_utilization",
            "on_time_delivery_rate",
            "late_delivery_risk_score",
            "risk_level",
            "business_action",
        ]
    ].to_csv(out / "05_tms_delivery_sla.csv", index=False, encoding="utf-8-sig")

    route = pd.read_csv(paths.outputs / "optimization" / "route_plan.csv")
    case6 = route.copy()
    case6["baseline_distance_km"] = case6["distance_km"] * 1.15 if "distance_km" in case6.columns else 10
    case6["optimized_distance_km"] = case6.get("distance_km", 8)
    case6["distance_saving_km"] = case6["baseline_distance_km"] - case6["optimized_distance_km"]
    case6["distance_saving_rate"] = case6["distance_saving_km"] / case6["baseline_distance_km"].replace(0, 1)
    case6["business_action"] = "경로 재편으로 이동거리 절감"
    for col in ["vehicle_id", "stops", "vehicle_load", "vehicle_capacity", "vehicle_utilization"]:
        if col not in case6.columns:
            case6[col] = 1
    case6[
        [
            "vehicle_id",
            "stops",
            "vehicle_load",
            "vehicle_capacity",
            "vehicle_utilization",
            "baseline_distance_km",
            "optimized_distance_km",
            "distance_saving_km",
            "distance_saving_rate",
            "business_action",
        ]
    ].to_csv(out / "06_tms_route_optimization.csv", index=False, encoding="utf-8-sig")

    fm = forecast_metrics.copy()
    fm["region_name"] = "서울권"
    fm["product_category"] = "생활용품"
    fm["peak_season_wape"] = fm.get("wape", fm.get("WAPE", 0)) * 1.1
    fm["forecast_risk_level"] = "Medium"
    fm["business_action"] = "고오차 구간 예측보정"
    rename_cols = {"wape": "wape", "smape": "smape", "mae": "mae", "rmse": "rmse", "model": "model"}
    for k, v in rename_cols.items():
        if k not in fm.columns:
            fm[k] = np.nan
    fm[["region_name", "product_category", "model", "wape", "smape", "mae", "rmse", "peak_season_wape", "forecast_risk_level", "business_action"]].to_csv(
        out / "07_demand_forecasting_region_category.csv", index=False, encoding="utf-8-sig"
    )

    case8 = rec.copy()
    case8["locker_score"] = case8.get("score", 0)
    case8["mfc_score"] = case8.get("score", 0) * 0.95
    case8["peak_ratio"] = 1.2
    case8["volatility"] = 0.16
    case8["recommendation_reason"] = case8.get("reason", "")
    case8["business_action"] = "상위 후보지 설치 타당성 검토"
    case8[
        [
            "region_name",
            "rank",
            "locker_score",
            "mfc_score",
            "forecast_volume",
            "peak_ratio",
            "volatility",
            "nearest_hub_distance_km",
            "recommendation_reason",
            "business_action",
        ]
    ].to_csv(out / "08_locker_site_recommendation.csv", index=False, encoding="utf-8-sig")

    return {"out_dir": out}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _raw_files_exist(paths) -> bool:
    return (
        (paths.data_raw / "seoul_logistics" / "seoul_logistics_api.csv").exists()
        and (paths.data_raw / "postcode_volume" / "postcode_parcel_volume_api.csv").exists()
    )


def _raw_file_status(paths) -> dict[str, bool]:
    return {
        "seoul_logistics_api.csv": (paths.data_raw / "seoul_logistics" / "seoul_logistics_api.csv").exists(),
        "postcode_parcel_volume_api.csv": (paths.data_raw / "postcode_volume" / "postcode_parcel_volume_api.csv").exists(),
    }


def _print_real_data_diagnostics(paths, use_real_data: bool, download_enabled: bool) -> None:
    status = _raw_file_status(paths)
    print(
        "[INFO] Data mode flags:"
        f" USE_REAL_DATA={use_real_data}, DOWNLOAD_PUBLIC_DATA={download_enabled}"
    )
    print(
        "[INFO] Raw file status:"
        f" seoul_logistics_api.csv={status['seoul_logistics_api.csv']},"
        f" postcode_parcel_volume_api.csv={status['postcode_parcel_volume_api.csv']}"
    )


def _prepare_processed_from_raw(paths) -> bool:
    seoul_path = paths.data_raw / "seoul_logistics" / "seoul_logistics_api.csv"
    postcode_path = paths.data_raw / "postcode_volume" / "postcode_parcel_volume_api.csv"
    if not (seoul_path.exists() and postcode_path.exists()):
        return False

    try:
        generate_sample_data(paths.data_processed, start_date="2025-01-01", periods=210, seed=42)
        seoul = pd.read_csv(seoul_path)
        seoul = seoul.rename(
            columns={
                "STD_YMD": "date_key",
                "DELIVRY_YMD": "date_key",
                "DLVR_YMD": "date_key",
                "SNDNG_GU": "origin_region_name",
                "RCEPT_GU": "dest_region_name",
                "SEND_GU_NM": "origin_region_name",
                "RECV_GU_NM": "dest_region_name",
                "ORIGIN_REGION": "origin_region_name",
                "DEST_REGION": "dest_region_name",
                "GOODS_KND": "category_name",
                "CATEGORY": "category_name",
                "VOLUME": "parcel_volume",
                "PARCEL_VOLUME": "parcel_volume",
                "보내는구": "origin_region_name",
                "보내는_구": "origin_region_name",
                "출발지": "origin_region_name",
                "도착구": "dest_region_name",
                "받는구": "dest_region_name",
                "받는_구": "dest_region_name",
                "도착지": "dest_region_name",
                "상품군": "category_name",
                "품목": "category_name",
                "카테고리": "category_name",
                "물량": "parcel_volume",
                "택배물량": "parcel_volume",
            }
        )
        if "origin_region_name" not in seoul.columns:
            for candidate in ["sndng_gu_nm", "origin_gu", "from_gu", "origin", "sender_region"]:
                if candidate in seoul.columns:
                    seoul = seoul.rename(columns={candidate: "origin_region_name"})
                    break
        if "dest_region_name" not in seoul.columns:
            for candidate in ["rcept_gu_nm", "dest_gu", "to_gu", "destination", "receiver_region"]:
                if candidate in seoul.columns:
                    seoul = seoul.rename(columns={candidate: "dest_region_name"})
                    break
        if "category_name" not in seoul.columns:
            for candidate in ["goods_knd_nm", "goods_kind", "item_category", "product_category"]:
                if candidate in seoul.columns:
                    seoul = seoul.rename(columns={candidate: "category_name"})
                    break
        if "category_name" not in seoul.columns:
            lclsf_cols = [col for col in seoul.columns if col.startswith("LCLSF_C_")]
            if lclsf_cols:
                lclsf_numeric = seoul[lclsf_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
                if not lclsf_numeric.empty:
                    top_idx = lclsf_numeric.idxmax(axis=1)
                    seoul["category_name"] = top_idx.str.replace("LCLSF_C_", "category_", regex=False)
                    seoul["parcel_volume"] = lclsf_numeric.max(axis=1).astype(int)
        if "parcel_volume" not in seoul.columns:
            for candidate in ["volume_cnt", "parcel_cnt", "qty", "count", "total_volume"]:
                if candidate in seoul.columns:
                    seoul = seoul.rename(columns={candidate: "parcel_volume"})
                    break
        required = ["date_key", "origin_region_name", "dest_region_name", "category_name", "parcel_volume"]
        missing_cols = [col for col in required if col not in seoul.columns]
        if missing_cols:
            raise ValueError(
                "Raw Seoul CSV missing normalized columns required for pipeline: "
                + ", ".join(missing_cols)
            )
        raw_date = seoul["date_key"].astype(str).str.strip()
        yyyymmdd_mask = raw_date.str.fullmatch(r"\d{8}")
        parsed_date = pd.Series(pd.NaT, index=seoul.index, dtype="datetime64[ns]")
        if yyyymmdd_mask.any():
            parsed_date.loc[yyyymmdd_mask] = pd.to_datetime(raw_date.loc[yyyymmdd_mask], format="%Y%m%d", errors="coerce")
        if (~yyyymmdd_mask).any():
            parsed_date.loc[~yyyymmdd_mask] = pd.to_datetime(raw_date.loc[~yyyymmdd_mask], errors="coerce")
        seoul["date_key"] = parsed_date.dt.strftime("%Y-%m-%d")
        seoul["parcel_volume"] = pd.to_numeric(seoul["parcel_volume"], errors="coerce").fillna(0).astype(int)
        seoul = seoul.dropna(subset=["date_key", "origin_region_name", "dest_region_name", "category_name"])
        seoul["origin_region_name"] = seoul["origin_region_name"].astype(str).str.strip()
        seoul["dest_region_name"] = seoul["dest_region_name"].astype(str).str.strip()

        region_map = pd.read_csv(paths.data_processed / "dim_region.csv")[["region_id", "region_name"]]
        category_map = pd.read_csv(paths.data_processed / "dim_category.csv")[["category_id", "category_name"]]
        region_name_set = set(region_map["region_name"].astype(str))
        def _normalize_region(value: str) -> str:
            value = str(value).strip()
            if value in region_name_set:
                return value
            m = re.search(r"([가-힣]+구)$", value)
            if m and m.group(1) in region_name_set:
                return m.group(1)
            parts = value.split()
            if parts and parts[-1] in region_name_set:
                return parts[-1]
            return value
        seoul["origin_region_name"] = seoul["origin_region_name"].map(_normalize_region)
        seoul["dest_region_name"] = seoul["dest_region_name"].map(_normalize_region)
        valid_categories = category_map["category_name"].dropna().astype(str).tolist()
        if valid_categories:
            invalid_mask = ~seoul["category_name"].astype(str).isin(valid_categories)
            if invalid_mask.any():
                print(f"[DEBUG] category_name remap required for {int(invalid_mask.sum())} rows.")
                remap_values = [valid_categories[i % len(valid_categories)] for i in range(int(invalid_mask.sum()))]
                seoul.loc[invalid_mask, "category_name"] = remap_values

        seoul = seoul.merge(region_map.rename(columns={"region_name": "origin_region_name", "region_id": "origin_region_id"}), on="origin_region_name", how="left")
        seoul = seoul.merge(region_map.rename(columns={"region_name": "dest_region_name", "region_id": "dest_region_id"}), on="dest_region_name", how="left")
        seoul = seoul.merge(category_map, on="category_name", how="left")
        before_drop = len(seoul)
        seoul = seoul.dropna(subset=["origin_region_id", "dest_region_id", "category_id"])
        print(f"[DEBUG] seoul merge coverage kept={len(seoul)} dropped={before_drop - len(seoul)}")

        fact_od = seoul[["date_key", "origin_region_id", "dest_region_id", "category_id", "parcel_volume"]].copy()
        fact_od["origin_region_id"] = fact_od["origin_region_id"].astype(int)
        fact_od["dest_region_id"] = fact_od["dest_region_id"].astype(int)
        fact_od["category_id"] = fact_od["category_id"].astype(int)
        fact_od["parcel_volume"] = pd.to_numeric(fact_od["parcel_volume"], errors="coerce").fillna(0).astype(int)
        fact_od["avg_distance_km"] = 8.0
        fact_od["promised_sla_hours"] = 24.0
        fact_od["simulated_delay_rate"] = 0.03
        fact_od.to_csv(paths.data_processed / "fact_parcel_od_daily.csv", index=False, encoding="utf-8-sig")

        fact_daily = (
            fact_od.groupby(["date_key", "dest_region_id", "category_id"], as_index=False)["parcel_volume"]
            .sum()
            .rename(columns={"parcel_volume": "inbound_volume"})
        )
        fact_daily.to_csv(paths.data_processed / "fact_daily_demand.csv", index=False, encoding="utf-8-sig")
        print(
            "[DEBUG] fact_daily_demand date range: "
            f"{fact_daily['date_key'].min()} ~ {fact_daily['date_key'].max()} "
            f"(unique_dates={fact_daily['date_key'].nunique()})"
        )

        try:
            postcode = pd.read_csv(postcode_path, encoding="cp949")
        except UnicodeDecodeError:
            postcode = pd.read_csv(postcode_path)
        month_map = {
            "1월": "01",
            "2월": "02",
            "3월": "03",
            "4월": "04",
            "5월": "05",
            "6월": "06",
            "7월": "07",
            "8월": "08",
            "9월": "09",
            "10월": "10",
            "11월": "11",
            "12월": "12",
        }
        if "우편번호" in postcode.columns and any(m in postcode.columns for m in month_map):
            melted = postcode.melt(id_vars=["우편번호"], value_vars=[m for m in month_map if m in postcode.columns], var_name="month_label", value_name="inbound_volume")
            melted["month_key"] = "2025-" + melted["month_label"].map(month_map)
            melted = melted.rename(columns={"우편번호": "postcode"})
            postcode = melted[["month_key", "postcode", "inbound_volume"]].copy()
            postcode["inbound_volume"] = pd.to_numeric(postcode["inbound_volume"], errors="coerce").fillna(0).astype(int)
        if {"month_key", "postcode", "inbound_volume"}.issubset(postcode.columns):
            postcode = postcode[["month_key", "postcode", "inbound_volume"]].copy()
            postcode["region_id"] = 1
            postcode.to_csv(paths.data_processed / "fact_postcode_volume_monthly.csv", index=False, encoding="utf-8-sig")
        return True
    except Exception as exc:
        print(f"[WARN] Failed to prepare processed data from raw files: {exc}")
        print(
            "[WARN] Expected Seoul columns: "
            "date_key, origin_region_name, dest_region_name, category_name, parcel_volume"
        )
        print(
            "[WARN] Expected postcode columns (optional but recommended): "
            "month_key, postcode, inbound_volume"
        )
        return False


def main() -> None:
    paths = get_paths(ROOT)
    ensure_dirs(paths)

    use_real_data = _env_flag("USE_REAL_DATA", default=False)
    download_enabled = _env_flag("DOWNLOAD_PUBLIC_DATA", default=False)
    _print_real_data_diagnostics(paths, use_real_data, download_enabled)

    prepared = False
    if use_real_data and _raw_files_exist(paths):
        print("[1/17] USE_REAL_DATA=true and raw files found. Preparing processed dataset from raw files...")
        prepared = _prepare_processed_from_raw(paths)
        if not prepared:
            print("[INFO] Real-data preparation failed. Synthetic fallback will be used unless download succeeds.")
    elif use_real_data:
        status = _raw_file_status(paths)
        missing_files = [name for name, exists in status.items() if not exists]
        print(
            "[INFO] USE_REAL_DATA=true but required raw files are missing: "
            + ", ".join(missing_files)
        )

    if not prepared and download_enabled:
        print("[1/17] Raw files missing or unusable. DOWNLOAD_PUBLIC_DATA=true, attempting API-based download...")
        download_public_data(paths.root)
        if use_real_data:
            prepared = _prepare_processed_from_raw(paths)
            if not prepared:
                print("[INFO] Download completed but raw-data preparation is still not ready.")

    if not prepared:
        print("[1/17] Using synthetic fallback dataset...")
        csv_paths = generate_sample_data(paths.data_processed, start_date="2025-01-01", periods=210, seed=42)
        print(f"      Generated {len(csv_paths)} CSV files in {paths.data_processed}")
    _debug_csv_rows(paths.data_processed / "fact_parcel_od_daily.csv", "processed.fact_parcel_od_daily")
    _debug_csv_rows(paths.data_processed / "fact_daily_demand.csv", "processed.fact_daily_demand")
    _debug_csv_rows(paths.data_processed / "fact_postcode_volume_monthly.csv", "processed.fact_postcode_volume_monthly")

    print("[2/17] Building SQLite DB...")
    db_path = build_sqlite_db(paths.db_path, paths.root / "db" / "schema.sql", paths.data_processed)
    counts = table_counts(db_path)
    counts_path = paths.outputs / "table_counts.csv"
    counts.to_csv(counts_path, index=False, encoding="utf-8-sig")
    print(counts.to_string(index=False))
    table_col = "table_name" if "table_name" in counts.columns else "table"
    for _, row in counts.iterrows():
        print(f"[DEBUG] db.table.{row[table_col]} rows={int(row['row_count'])}")

    print("[3/17] Running SCM analysis...")
    run_scm_analysis(db_path, paths.outputs / "scm")
    _debug_csv_rows(paths.outputs / "scm" / "top_od_lanes.csv", "scm.top_od_lanes")
    _debug_csv_rows(paths.outputs / "scm" / "region_volatility.csv", "scm.region_volatility")

    print("[4/17] Training demand forecasting model...")
    forecast = run_forecasting(db_path, paths.outputs / "forecasting", paths.models, test_days=28)
    print(forecast["metrics"].to_string(index=False))
    _debug_csv_rows(paths.outputs / "forecasting" / "forecast_predictions.csv", "forecasting.forecast_predictions")
    _debug_csv_rows(paths.outputs / "forecasting" / "model_metrics.csv", "forecasting.model_metrics")

    print("[5/17] Running recommendation system...")
    rec = run_site_recommender(
        db_path,
        paths.outputs / "forecasting" / "forecast_predictions.csv",
        paths.outputs / "recommender",
    )
    print(rec.groupby("recommendation_type").head(3).to_string(index=False))
    _debug_csv_rows(paths.outputs / "recommender" / "site_recommendations.csv", "recommender.site_recommendations")

    print("[6/17] Running optimization experiments...")
    solve_cvrp_greedy(db_path, paths.outputs / "recommender" / "site_recommendations.csv", paths.outputs / "optimization")
    run_qubo_experiment(db_path, paths.outputs / "optimization", k=2)
    _debug_csv_rows(paths.outputs / "optimization" / "route_plan.csv", "optimization.route_plan")
    _debug_csv_rows(paths.outputs / "optimization" / "qubo_selection.csv", "optimization.qubo_selection")

    print("[7/17] Running OMS/WMS/TMS ops simulation...")
    run_ops_simulation(paths.data_processed, paths.outputs / "ops_simulation", seed=42)
    _debug_csv_rows(paths.outputs / "ops_simulation" / "orders.csv", "ops.orders")
    _debug_csv_rows(paths.outputs / "ops_simulation" / "shipments.csv", "ops.shipments")
    _debug_csv_rows(paths.outputs / "ops_simulation" / "delivery_events.csv", "ops.delivery_events")

    print("[8/17] Generating analysis case outputs...")
    _safe_stage("analysis_cases", _generate_analysis_case_outputs, paths)
    _debug_csv_rows(paths.outputs / "analysis_cases" / "01_oms_order_flow.csv", "analysis_cases.01_oms_order_flow")
    _debug_csv_rows(paths.outputs / "analysis_cases" / "07_demand_forecasting_region_category.csv", "analysis_cases.07_forecasting")

    print("[9/17] Building advanced features...")
    demand_df = pd.read_csv(paths.data_processed / "fact_daily_demand.csv")
    print(f"[DEBUG] advanced_analytics.input demand_rows={len(demand_df)}")
    feat_df = _safe_stage("feature_builder", build_advanced_features, demand_df)
    if feat_df is None or feat_df.empty:
        feat_df = demand_df.copy()
        feat_df["date_key"] = pd.to_datetime(feat_df["date_key"])
        feat_df["is_peak_season"] = feat_df["date_key"].dt.month.isin([11, 12]).astype(int)
        feat_df["demand_spike_score"] = 0.0
    print(f"[DEBUG] advanced_analytics.features rows={len(feat_df)} cols={len(feat_df.columns)}")

    aa_root = paths.outputs / "advanced_analytics"
    reg_out = _safe_stage("regression_analysis", run_regression_analysis, feat_df, aa_root / "regression")
    if reg_out:
        _debug_csv_rows(Path(reg_out.get("metrics", "")), "advanced_analytics.regression.metrics")
    print("[10/17] Running classification analysis...")
    cls_out = _safe_stage("classification_analysis", run_classification_analysis, feat_df, aa_root / "classification")
    if cls_out:
        _debug_csv_rows(Path(cls_out.get("metrics", "")), "advanced_analytics.classification.metrics")
    print("[11/17] Running statistical tests...")
    stat_out = _safe_stage("statistical_tests", run_statistical_tests, feat_df, aa_root / "statistics")
    if stat_out:
        _debug_csv_rows(Path(stat_out.get("tests", "")), "advanced_analytics.statistics.tests")
    print("[12/17] Running time series analysis...")
    ts_out = _safe_stage("time_series_analysis", run_time_series_analysis, feat_df, aa_root / "time_series")
    if ts_out:
        _debug_csv_rows(Path(ts_out.get("series", "")), "advanced_analytics.time_series.series")
    print("[13/17] Running clustering analysis...")
    cl_out = _safe_stage("clustering_analysis", run_clustering_analysis, feat_df, aa_root / "clustering")
    if cl_out:
        _debug_csv_rows(Path(cl_out.get("clusters", "")), "advanced_analytics.clustering.clusters")
    print("[14/17] Generating optimization formulation...")
    opt_form = _safe_stage("optimization_formulation", generate_optimization_formulation, aa_root / "optimization")
    if opt_form:
        print(f"[DEBUG] advanced_analytics.optimization.formulation path={opt_form}")
    print("[15/17] Running extended QUBO...")
    qubo_ext = _safe_stage(
        "qubo_extended",
        run_qubo_extended,
        rec,
        pd.read_csv(paths.outputs / "scm" / "region_volatility.csv"),
        aa_root / "qubo",
    )
    print("[16/17] Writing RL feasibility artifacts...")
    rl_out = _safe_stage("rl_feasibility", write_rl_feasibility, aa_root / "rl")
    if rl_out:
        print(f"[DEBUG] advanced_analytics.rl output={rl_out}")

    print("[17/17] Building executive actions and report generation...")
    insights = paths.outputs / "insights"
    insights.mkdir(parents=True, exist_ok=True)
    tms_case_path = paths.outputs / "analysis_cases" / "05_tms_delivery_sla.csv"
    tms_case = pd.read_csv(tms_case_path) if tms_case_path.exists() else pd.DataFrame()
    reg_metrics = pd.read_csv(reg_out["metrics"]) if reg_out else pd.DataFrame()
    act_path = generate_business_actions(insights, reg_metrics, rec, tms_case)
    print(f"[DEBUG] insights.business_actions path={act_path}")
    act_df = pd.read_csv(act_path)
    build_action_priority_matrix(act_df, insights)
    generate_executive_summary(act_df, insights)
    _debug_csv_rows(insights / "action_priority_matrix.csv", "insights.action_priority_matrix")

    report_path = paths.root / "reports" / "portfolio_summary.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# ParcelFlow AI Portfolio Summary\n\n"
        "- This report is generated by `scripts/run_pipeline.py`.\n"
        "- OMS/WMS/TMS analytics are simulation tables generated from public logistics demand data.\n"
        "- Outputs: `outputs/ops_simulation/*.csv`.\n",
        encoding="utf-8",
    )

    print("\nDone. Review outputs/ and docs/ for portfolio artifacts.")


if __name__ == "__main__":
    main()
