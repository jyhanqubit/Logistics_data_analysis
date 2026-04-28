from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_external_seoul_logistics_csv(csv_path: Path) -> pd.DataFrame:
    """Placeholder adapter for real Seoul logistics public data.

    실제 공개데이터 CSV 컬럼명은 데이터셋/다운로드 방식에 따라 달라질 수 있으므로,
    Codex에게 실제 파일 샘플을 보여주고 이 adapter를 수정하도록 요청하면 됩니다.

    Expected normalized columns:
        - date_key
        - origin_region_name
        - dest_region_name
        - category_name
        - parcel_volume
    """
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(csv_path)
    # TODO: map real public-data columns to normalized schema.
    required = {"date_key", "origin_region_name", "dest_region_name", "category_name", "parcel_volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            "External CSV is not normalized yet. Missing columns: "
            + ", ".join(sorted(missing))
            + ". Use Codex prompt .codex/prompts/01_data_engineering.md to implement mapping."
        )
    return df
