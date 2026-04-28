from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

TABLE_LOAD_ORDER = [
    "dim_calendar",
    "dim_region",
    "dim_category",
    "dim_hub_candidate",
    "fact_parcel_od_daily",
    "fact_postcode_volume_monthly",
    "fact_daily_demand",
]


def build_sqlite_db(db_path: Path, schema_path: Path, csv_dir: Path) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        schema = schema_path.read_text(encoding="utf-8")
        conn.executescript(schema)
        for table in TABLE_LOAD_ORDER:
            csv_path = csv_dir / f"{table}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing required CSV for table {table}: {csv_path}")
            df = pd.read_csv(csv_path)
            df.to_sql(table, conn, if_exists="append", index=False)
        conn.commit()
    return db_path


def query_df(db_path: Path, sql: str, params: tuple | None = None) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params or ())


def table_counts(db_path: Path) -> pd.DataFrame:
    rows = []
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for table in TABLE_LOAD_ORDER:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            rows.append({"table": table, "row_count": int(cur.fetchone()[0])})
    return pd.DataFrame(rows)
