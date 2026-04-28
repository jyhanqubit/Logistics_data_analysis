from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parcelflow.data_generator import generate_sample_data
from parcelflow.db import build_sqlite_db, table_counts
from parcelflow.forecasting import run_forecasting


def test_small_pipeline_smoke(tmp_path: Path) -> None:
    csv_dir = tmp_path / "csv"
    out_dir = tmp_path / "out"
    model_dir = tmp_path / "models"
    db_path = tmp_path / "parcelflow.sqlite"
    generate_sample_data(csv_dir, periods=55, seed=7)
    build_sqlite_db(db_path, ROOT / "db" / "schema.sql", csv_dir)
    counts = table_counts(db_path)
    assert counts["row_count"].min() > 0
    result = run_forecasting(db_path, out_dir / "forecasting", model_dir, test_days=14)
    assert not result["metrics"].empty
    assert (out_dir / "forecasting" / "forecast_predictions.csv").exists()
