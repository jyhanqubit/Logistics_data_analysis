from __future__ import annotations

import io
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .data_go_kr import download_postcode_parcel_volume
from .file_utils import ensure_dir, read_csv_with_encoding_fallback, save_dataframe_csv, safe_request_get
from .seoul_open_data import SeoulOpenDataClient


def _normalize_seoul_logistics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    renamed = df.rename(
        columns={
            "STD_YMD": "date_key",
            "DELIVRY_YMD": "date_key",
            "DLVR_YMD": "date_key",
            "SNDNG_GU": "origin_region_name",
            "RCEPT_GU": "dest_region_name",
            "ORIGIN_REGION": "origin_region_name",
            "DEST_REGION": "dest_region_name",
            "GOODS_KND": "category_name",
            "CATEGORY": "category_name",
            "VOLUME": "parcel_volume",
            "PARCEL_VOLUME": "parcel_volume",
        }
    )
    needed = ["date_key", "origin_region_name", "dest_region_name", "category_name", "parcel_volume"]
    missing = [col for col in needed if col not in renamed.columns]
    if missing:
        raise ValueError(
            "Seoul logistics API/CSV schema is not normalized. Missing columns: "
            + ", ".join(missing)
            + ". Provide SEOUL_LOGISTICS_SERVICE_NAME or fallback CSV URLs that can map to required columns."
        )
    normalized = renamed[needed].copy()
    raw_date = normalized["date_key"].astype(str).str.strip()
    yyyymmdd_mask = raw_date.str.fullmatch(r"\d{8}")
    parsed = pd.Series(pd.NaT, index=normalized.index, dtype="datetime64[ns]")
    if yyyymmdd_mask.any():
        parsed.loc[yyyymmdd_mask] = pd.to_datetime(raw_date.loc[yyyymmdd_mask], format="%Y%m%d", errors="coerce")
    if (~yyyymmdd_mask).any():
        parsed.loc[~yyyymmdd_mask] = pd.to_datetime(raw_date.loc[~yyyymmdd_mask], errors="coerce")
    normalized["date_key"] = parsed.dt.strftime("%Y-%m-%d")
    normalized["parcel_volume"] = pd.to_numeric(normalized["parcel_volume"], errors="coerce").fillna(0).astype(int)
    return normalized.dropna(subset=["date_key", "origin_region_name", "dest_region_name", "category_name"])


def _download_configured_csvs(urls_env: str = "SEOUL_LOGISTICS_MONTHLY_CSV_URLS") -> pd.DataFrame:
    urls = [u.strip() for u in os.getenv(urls_env, "").split(",") if u.strip()]
    if not urls:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for url in urls:
        response = safe_request_get(url)
        frames.append(pd.read_csv(io.StringIO(response.text)))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _date_range_yyyymmdd(start_yyyymmdd: str, end_yyyymmdd: str) -> list[str]:
    start = datetime.strptime(start_yyyymmdd, "%Y%m%d")
    end = datetime.strptime(end_yyyymmdd, "%Y%m%d")
    if start > end:
        raise ValueError("SEOUL_DLVR_YMD_START must be <= SEOUL_DLVR_YMD_END.")

    current = start
    dates: list[str] = []
    while current <= end:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return dates


def _download_seoul_api_dataset(service_name: str) -> pd.DataFrame:
    client = SeoulOpenDataClient()
    date_start = os.getenv("SEOUL_DLVR_YMD_START", "").strip()
    date_end = os.getenv("SEOUL_DLVR_YMD_END", "").strip()
    progress_every = int(os.getenv("SEOUL_PROGRESS_EVERY", "10").strip() or "10")

    if date_start and date_end:
        frames: list[pd.DataFrame] = []
        target_dates = _date_range_yyyymmdd(date_start, date_end)
        total_days = len(target_dates)
        print(f"[INFO] Seoul API date-range mode enabled: {date_start}~{date_end} ({total_days} days)")

        for idx, yyyymmdd in enumerate(target_dates, start=1):
            if idx == 1 or idx == total_days or (progress_every > 0 and idx % progress_every == 0):
                print(f"[INFO] Seoul API progress {idx}/{total_days} (DLVR_YMD={yyyymmdd})")
            try:
                day_df = client.fetch_service_rows(service_name, extra_path_segments=[yyyymmdd])
                if not day_df.empty:
                    frames.append(day_df)
            except Exception as exc:
                print(f"[WARN] Seoul API call failed for DLVR_YMD={yyyymmdd}: {exc}")

        merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        print(f"[INFO] Seoul API date-range collection completed. merged_rows={len(merged)}")
        return merged

    return client.fetch_service_rows(service_name)


def _synthetic_seoul_logistics(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-01-01", periods=90, freq="D")
    regions = ["강남구", "마포구", "송파구", "강서구"]
    categories = ["생활용품", "식품/신선", "패션/잡화"]
    rows: list[dict] = []
    for date in dates:
        for origin in regions:
            for dest in regions:
                if origin == dest:
                    continue
                rows.append(
                    {
                        "date_key": date.strftime("%Y-%m-%d"),
                        "origin_region_name": origin,
                        "dest_region_name": dest,
                        "category_name": categories[rng.integers(0, len(categories))],
                        "parcel_volume": int(max(0, rng.normal(120, 30))),
                    }
                )
    return pd.DataFrame(rows)


def _synthetic_postcode_volume(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    months = pd.period_range("2025-01", periods=6, freq="M")
    postcodes = ["06236", "04147", "05510", "07803"]
    rows = []
    for month in months:
        for postcode in postcodes:
            rows.append(
                {
                    "month_key": str(month),
                    "postcode": postcode,
                    "inbound_volume": int(max(0, rng.normal(6000, 1200))),
                }
            )
    return pd.DataFrame(rows)


def download_public_data(root: Path) -> dict[str, Path | None]:
    raw_root = ensure_dir(root / "data" / "raw")
    seoul_dir = ensure_dir(raw_root / "seoul_logistics")
    postcode_dir = ensure_dir(raw_root / "postcode_volume")

    outputs: dict[str, Path | None] = {"seoul_logistics": None, "postcode_volume": None}
    force_refresh = os.getenv("DOWNLOAD_FORCE_REFRESH", "false").strip().lower() == "true"

    service_name = os.getenv("SEOUL_LOGISTICS_SERVICE_NAME", "").strip()
    seoul_path = seoul_dir / "seoul_logistics_api.csv"
    if seoul_path.exists() and not force_refresh:
        try:
            existing_seoul = read_csv_with_encoding_fallback(seoul_path)
            if not existing_seoul.empty:
                print(f"[INFO] Reusing existing Seoul raw file: {seoul_path}")
                outputs["seoul_logistics"] = seoul_path
            else:
                print(f"[WARN] Existing Seoul file is empty. Refreshing: {seoul_path}")
        except Exception as exc:
            print(f"[WARN] Failed to read existing Seoul file. Refreshing. Details: {exc}")

    seoul_df = pd.DataFrame()
    if outputs["seoul_logistics"] is None:
        if service_name:
            try:
                seoul_df = _download_seoul_api_dataset(service_name)
                seoul_df = _normalize_seoul_logistics(seoul_df)
            except Exception as exc:
                print(f"[WARN] Seoul Open API download failed: {exc}")
        else:
            print("[WARN] SEOUL_LOGISTICS_SERVICE_NAME is empty; skipping Seoul API call and trying fallback.")

        if seoul_df.empty:
            try:
                csv_df = _download_configured_csvs()
                if not csv_df.empty:
                    seoul_df = _normalize_seoul_logistics(csv_df)
            except Exception as exc:
                print(f"[WARN] Seoul monthly CSV fallback failed: {exc}")

        if seoul_df.empty:
            print("[INFO] Using synthetic fallback for Seoul logistics dataset.")
            seoul_df = _synthetic_seoul_logistics()

        outputs["seoul_logistics"] = save_dataframe_csv(seoul_df, seoul_path)

    postcode_path = postcode_dir / "postcode_parcel_volume_api.csv"
    if postcode_path.exists() and not force_refresh:
        try:
            existing_postcode = read_csv_with_encoding_fallback(postcode_path)
            if not existing_postcode.empty:
                print(f"[INFO] Reusing existing postcode raw file: {postcode_path}")
                outputs["postcode_volume"] = postcode_path
            else:
                print(f"[WARN] Existing postcode file is empty. Refreshing: {postcode_path}")
        except Exception as exc:
            print(f"[WARN] Failed to read existing postcode file. Refreshing. Details: {exc}")

    endpoint = os.getenv("DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT", "").strip()
    postcode_df = pd.DataFrame()
    if outputs["postcode_volume"] is None:
        if endpoint:
            try:
                postcode_df = download_postcode_parcel_volume(endpoint)
            except Exception as exc:
                print(f"[WARN] data.go.kr postcode API download failed: {exc}")
        else:
            print("[WARN] DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT is empty; skipping API call.")

        if postcode_df.empty:
            print("[INFO] Using synthetic fallback for postcode parcel volume dataset.")
            postcode_df = _synthetic_postcode_volume()

        if "month_key" not in postcode_df.columns:
            postcode_df["month_key"] = pd.Timestamp.today().strftime("%Y-%m")
        if "postcode" not in postcode_df.columns:
            postcode_df["postcode"] = "00000"
        if "inbound_volume" not in postcode_df.columns:
            postcode_df["inbound_volume"] = 0

        postcode_df["inbound_volume"] = pd.to_numeric(postcode_df["inbound_volume"], errors="coerce").fillna(0).astype(int)
        postcode_df = postcode_df[["month_key", "postcode", "inbound_volume"]].copy()
        outputs["postcode_volume"] = save_dataframe_csv(postcode_df, postcode_path)

    return outputs


__all__ = ["SeoulOpenDataClient", "download_postcode_parcel_volume", "download_public_data"]
