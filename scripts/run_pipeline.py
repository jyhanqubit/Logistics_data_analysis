from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parcelflow.config import ensure_dirs, get_paths
from parcelflow.data_generator import generate_sample_data
from parcelflow.db import build_sqlite_db, table_counts
from parcelflow.forecasting import run_forecasting
from parcelflow.optimization import run_qubo_experiment, solve_cvrp_greedy
from parcelflow.recommender import run_site_recommender
from parcelflow.scm_analysis import run_scm_analysis


def main() -> None:
    paths = get_paths(ROOT)
    ensure_dirs(paths)
    print("[1/6] Generating public-data-shaped sample logistics data...")
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
