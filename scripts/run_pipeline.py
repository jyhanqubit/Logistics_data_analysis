from __future__ import annotations

import os
import sys
from pathlib import Path

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
from parcelflow.recommender import run_site_recommender
from parcelflow.scm_analysis import run_scm_analysis


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def _raw_files_exist(paths) -> bool:
    return (
        (paths.data_raw / "seoul_logistics" / "seoul_logistics_api.csv").exists()
        and (paths.data_raw / "postcode_volume" / "postcode_parcel_volume_api.csv").exists()
    )


def _prepare_processed_from_raw(paths) -> bool:
    seoul_path = paths.data_raw / "seoul_logistics" / "seoul_logistics_api.csv"
    postcode_path = paths.data_raw / "postcode_volume" / "postcode_parcel_volume_api.csv"
    if not (seoul_path.exists() and postcode_path.exists()):
        return False

    try:
        generate_sample_data(paths.data_processed, start_date="2025-01-01", periods=210, seed=42)
        seoul = pd.read_csv(seoul_path)
        required = ["date_key", "origin_region_name", "dest_region_name", "category_name", "parcel_volume"]
        if any(col not in seoul.columns for col in required):
            raise ValueError("Raw Seoul CSV missing normalized columns required for pipeline.")

        region_map = pd.read_csv(paths.data_processed / "dim_region.csv")[["region_id", "region_name"]]
        category_map = pd.read_csv(paths.data_processed / "dim_category.csv")[["category_id", "category_name"]]

        seoul = seoul.merge(region_map.rename(columns={"region_name": "origin_region_name", "region_id": "origin_region_id"}), on="origin_region_name", how="left")
        seoul = seoul.merge(region_map.rename(columns={"region_name": "dest_region_name", "region_id": "dest_region_id"}), on="dest_region_name", how="left")
        seoul = seoul.merge(category_map, on="category_name", how="left")
        seoul = seoul.dropna(subset=["origin_region_id", "dest_region_id", "category_id"])

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

        postcode = pd.read_csv(postcode_path)
        if {"month_key", "postcode", "inbound_volume"}.issubset(postcode.columns):
            postcode = postcode[["month_key", "postcode", "inbound_volume"]].copy()
            postcode["region_id"] = 1
            postcode.to_csv(paths.data_processed / "fact_postcode_volume_monthly.csv", index=False, encoding="utf-8-sig")
        return True
    except Exception as exc:
        print(f"[WARN] Failed to prepare processed data from raw files: {exc}")
        return False


def main() -> None:
    paths = get_paths(ROOT)
    ensure_dirs(paths)

    use_real_data = _env_flag("USE_REAL_DATA", default=False)
    download_enabled = _env_flag("DOWNLOAD_PUBLIC_DATA", default=False)

    prepared = False
    if use_real_data and _raw_files_exist(paths):
        print("[1/6] USE_REAL_DATA=true and raw files found. Preparing processed dataset from raw files...")
        prepared = _prepare_processed_from_raw(paths)

    if not prepared and download_enabled:
        print("[1/6] Raw files missing or unusable. DOWNLOAD_PUBLIC_DATA=true, attempting API-based download...")
        download_public_data(paths.root)
        if use_real_data:
            prepared = _prepare_processed_from_raw(paths)

    if not prepared:
        print("[1/6] Using synthetic fallback dataset...")
        csv_paths = generate_sample_data(paths.data_processed, start_date="2025-01-01", periods=210, seed=42)
        print(f"      Generated {len(csv_paths)} CSV files in {paths.data_processed}")

    print("[2/6] Building SQLite DB...")
    db_path = build_sqlite_db(paths.db_path, paths.root / "db" / "schema.sql", paths.data_processed)
    counts = table_counts(db_path)
    counts_path = paths.outputs / "table_counts.csv"
    counts.to_csv(counts_path, index=False, encoding="utf-8-sig")
    print(counts.to_string(index=False))

    print("[3/6] Running SCM analysis...")
    run_scm_analysis(db_path, paths.outputs / "scm")

    print("[4/6] Training demand forecasting model...")
    forecast = run_forecasting(db_path, paths.outputs / "forecasting", paths.models, test_days=28)
    print(forecast["metrics"].to_string(index=False))

    print("[5/6] Running recommendation system...")
    rec = run_site_recommender(
        db_path,
        paths.outputs / "forecasting" / "forecast_predictions.csv",
        paths.outputs / "recommender",
    )
    print(rec.groupby("recommendation_type").head(3).to_string(index=False))

    print("[6/6] Running optimization experiments...")
    solve_cvrp_greedy(db_path, paths.outputs / "recommender" / "site_recommendations.csv", paths.outputs / "optimization")
    run_qubo_experiment(db_path, paths.outputs / "optimization", k=2)

    print("\nDone. Review outputs/ and docs/ for portfolio artifacts.")


if __name__ == "__main__":
    main()
