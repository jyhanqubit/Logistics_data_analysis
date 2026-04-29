from __future__ import annotations

import re
import pandas as pd

SEOUL_DISTRICTS = {
    "강남구","강동구","강북구","강서구","관악구","광진구","구로구","금천구","노원구","도봉구","동대문구","동작구","마포구","서대문구","서초구","성동구","성북구","송파구","양천구","영등포구","용산구","은평구","종로구","중구","중랑구"
}


def assert_no_placeholder_text(df: pd.DataFrame) -> None:
    tokens = {"Action", "사유 정보 없음", "Region-1", "Region-2", "Cluster-0", "서울권"}
    text = df.astype(str)
    assert ~text.isin(tokens).any().any()


def assert_metric_not_all_zero(df: pd.DataFrame, col: str) -> None:
    assert col in df.columns
    assert not (pd.to_numeric(df[col], errors="coerce").fillna(0) == 0).all()


def assert_metric_not_all_one(df: pd.DataFrame, col: str) -> None:
    assert col in df.columns
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    assert not ((s >= 0.999).all())


def assert_min_unique_values(df: pd.DataFrame, col: str, min_unique: int) -> None:
    assert df[col].nunique() >= min_unique


def assert_region_names_are_real_seoul_districts(df: pd.DataFrame, col: str = "region_name") -> None:
    assert set(df[col].astype(str).unique()).issubset(SEOUL_DISTRICTS)


def assert_business_actions_are_specific(df: pd.DataFrame) -> None:
    assert df["recommended_action"].notna().all()
    assert ~df["recommended_action"].astype(str).isin(["Action", "사유 정보 없음"]).any()
    assert df["business_finding"].astype(str).str.contains(r"\d", regex=True).all()
