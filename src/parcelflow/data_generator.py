from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


SEOUL_REGIONS = [
    (1, "강남구", 37.5172, 127.0473, 561052, 1.38, 1.45),
    (2, "강동구", 37.5301, 127.1238, 463998, 1.05, 1.03),
    (3, "강북구", 37.6396, 127.0257, 291384, 0.82, 0.78),
    (4, "강서구", 37.5509, 126.8495, 574315, 1.15, 0.98),
    (5, "관악구", 37.4784, 126.9516, 487815, 1.12, 0.85),
    (6, "광진구", 37.5385, 127.0823, 337416, 1.01, 0.93),
    (7, "구로구", 37.4955, 126.8875, 395315, 1.00, 0.90),
    (8, "금천구", 37.4569, 126.8955, 229642, 0.84, 0.86),
    (9, "노원구", 37.6542, 127.0568, 503734, 0.96, 0.88),
    (10, "도봉구", 37.6688, 127.0471, 308627, 0.80, 0.80),
    (11, "동대문구", 37.5744, 127.0396, 342837, 0.96, 0.85),
    (12, "동작구", 37.5124, 126.9393, 380596, 1.02, 0.95),
    (13, "마포구", 37.5663, 126.9019, 364638, 1.24, 1.08),
    (14, "서대문구", 37.5791, 126.9368, 305946, 0.98, 0.93),
    (15, "서초구", 37.4837, 127.0324, 408451, 1.23, 1.42),
    (16, "성동구", 37.5633, 127.0369, 285543, 1.09, 1.02),
    (17, "성북구", 37.5894, 127.0167, 430528, 0.94, 0.88),
    (18, "송파구", 37.5145, 127.1059, 658338, 1.32, 1.22),
    (19, "양천구", 37.5170, 126.8665, 436028, 1.00, 1.00),
    (20, "영등포구", 37.5264, 126.8963, 376837, 1.18, 1.04),
    (21, "용산구", 37.5326, 126.9905, 218650, 1.10, 1.25),
    (22, "은평구", 37.6027, 126.9291, 465982, 0.94, 0.86),
    (23, "종로구", 37.5735, 126.9788, 141379, 0.86, 1.08),
    (24, "중구", 37.5636, 126.9976, 120437, 0.90, 1.14),
    (25, "중랑구", 37.6063, 127.0925, 384272, 0.88, 0.82),
]

CATEGORIES = [
    (1, "패션/잡화", 0.10, 0.20),
    (2, "식품/신선", 0.95, 0.25),
    (3, "생활용품", 0.20, 0.35),
    (4, "전자/가전", 0.05, 0.60),
    (5, "도서/문구", 0.05, 0.10),
]

HUB_CANDIDATES = [
    (1, "서북권 MFC 후보", 13, 37.5663, 126.9019, 52000, 0.70),
    (2, "동북권 MFC 후보", 9, 37.6542, 127.0568, 56000, 0.62),
    (3, "동남권 MFC 후보", 18, 37.5145, 127.1059, 72000, 0.95),
    (4, "서남권 MFC 후보", 4, 37.5509, 126.8495, 68000, 0.78),
    (5, "중부권 MFC 후보", 24, 37.5636, 126.9976, 48000, 0.85),
]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _calendar(start_date: str, periods: int) -> pd.DataFrame:
    dates = pd.date_range(start_date, periods=periods, freq="D")
    # 명절/쇼핑 시즌을 모사하는 간단 휴일 플래그
    holidays = set(pd.to_datetime(["2025-01-01", "2025-01-28", "2025-01-29", "2025-01-30", "2025-05-05", "2025-10-03", "2025-10-06", "2025-10-07", "2025-10-08", "2025-12-25"]))
    return pd.DataFrame({
        "date_key": dates.strftime("%Y-%m-%d"),
        "year": dates.year,
        "month": dates.month,
        "day": dates.day,
        "day_of_week": dates.dayofweek,
        "is_weekend": dates.dayofweek.isin([5, 6]).astype(int),
        "is_holiday": dates.isin(holidays).astype(int),
        "week_of_year": dates.isocalendar().week.astype(int),
    })


def make_dimensions() -> dict[str, pd.DataFrame]:
    return {
        "dim_region": pd.DataFrame(SEOUL_REGIONS, columns=["region_id", "region_name", "lat", "lon", "population", "ecommerce_index", "income_index"]),
        "dim_category": pd.DataFrame(CATEGORIES, columns=["category_id", "category_name", "perishability_score", "bulky_score"]),
        "dim_hub_candidate": pd.DataFrame(HUB_CANDIDATES, columns=["hub_id", "hub_name", "region_id", "lat", "lon", "capacity_daily", "fixed_cost_score"]),
    }


def generate_sample_data(output_dir: Path, start_date: str = "2025-01-01", periods: int = 210, seed: int = 42) -> dict[str, Path]:
    """Generate public-data-shaped sample logistics data.

    The generator intentionally creates realistic seasonality and regional skew while remaining synthetic.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    dims = make_dimensions()
    calendar = _calendar(start_date, periods)
    dims["dim_calendar"] = calendar
    regions = dims["dim_region"]
    categories = dims["dim_category"]
    region_by_id = {int(row["region_id"]): row for _, row in regions.iterrows()}

    # Precompute origin attractiveness and destination demand propensity
    origin_weights = regions["population"].to_numpy() * regions["ecommerce_index"].to_numpy()
    origin_weights = origin_weights / origin_weights.sum()
    dest_base = (regions["population"] / regions["population"].mean()) * regions["ecommerce_index"]
    category_multiplier = {
        1: 1.20,  # 패션
        2: 1.05,  # 식품
        3: 1.35,  # 생활용품
        4: 0.55,  # 전자
        5: 0.45,  # 도서
    }

    od_rows: list[dict] = []
    daily_rows: list[dict] = []

    for _, cal in calendar.iterrows():
        date = pd.Timestamp(cal["date_key"])
        dow = int(cal["day_of_week"])
        month = int(cal["month"])
        # 월요일/화요일 피크, 주말 하락, 5/11/12 쇼핑 시즌 상승
        dow_factor = {0: 1.18, 1: 1.11, 2: 1.02, 3: 1.00, 4: 1.04, 5: 0.82, 6: 0.78}[dow]
        seasonal_factor = 1.0 + 0.08 * math.sin(2 * math.pi * (date.dayofyear / 365.0))
        if month in [5, 11, 12]:
            seasonal_factor *= 1.13
        if int(cal["is_holiday"]):
            seasonal_factor *= 0.72
        if date.day in [1, 11, 21]:
            seasonal_factor *= 1.05

        for _, dest in regions.iterrows():
            region_id = int(dest["region_id"])
            region_factor = float(dest_base.loc[dest.name])
            # 지역별 트렌드: 강남/송파/마포/강서 등 증가세 모사
            growth_signal = 1.0 + (periods and (date - pd.Timestamp(start_date)).days / periods) * (float(dest["ecommerce_index"]) - 0.9) * 0.20
            for _, cat in categories.iterrows():
                category_id = int(cat["category_id"])
                cat_factor = category_multiplier[category_id]
                category_season = 1.0
                if category_id == 1 and month in [3, 4, 9, 10, 11]:
                    category_season *= 1.20
                if category_id == 2 and dow in [0, 1, 2]:
                    category_season *= 1.12
                if category_id == 4 and month in [11, 12]:
                    category_season *= 1.25
                mean_volume = 215 * region_factor * cat_factor * dow_factor * seasonal_factor * category_season * growth_signal
                inbound = int(max(0, rng.poisson(mean_volume)))
                daily_rows.append({
                    "date_key": cal["date_key"],
                    "dest_region_id": region_id,
                    "category_id": category_id,
                    "inbound_volume": inbound,
                })

                # OD는 상위 origin 일부만 생성해 데이터 크기를 관리한다.
                if inbound <= 0:
                    continue
                origin_ids = rng.choice(regions["region_id"].to_numpy(), size=4, replace=False, p=origin_weights)
                shares = rng.dirichlet(np.ones(len(origin_ids)) * 1.4)
                for origin_id, share in zip(origin_ids, shares):
                    origin = region_by_id[int(origin_id)]
                    vol = int(round(inbound * share))
                    if vol <= 0:
                        continue
                    distance = haversine_km(float(origin["lat"]), float(origin["lon"]), float(dest["lat"]), float(dest["lon"]))
                    promised = 24.0 if category_id != 2 else 12.0
                    delay_rate = min(0.35, max(0.01, 0.015 + (distance / 120) + (vol / 5000) + (0.03 if int(cal["day_of_week"]) == 0 else 0)))
                    od_rows.append({
                        "date_key": cal["date_key"],
                        "origin_region_id": int(origin_id),
                        "dest_region_id": region_id,
                        "category_id": category_id,
                        "parcel_volume": vol,
                        "avg_distance_km": round(distance, 3),
                        "promised_sla_hours": promised,
                        "simulated_delay_rate": round(delay_rate, 4),
                    })

    fact_daily = pd.DataFrame(daily_rows)
    fact_od = pd.DataFrame(od_rows)

    # Monthly postcode-level sample. Fake postcodes are generated for portfolio reproducibility.
    postcode_rows = []
    monthly = fact_daily.assign(month_key=fact_daily["date_key"].str.slice(0, 7)).groupby(["month_key", "dest_region_id"], as_index=False)["inbound_volume"].sum()
    for _, row in monthly.iterrows():
        region_id = int(row["dest_region_id"])
        total = int(row["inbound_volume"])
        weights = rng.dirichlet(np.ones(4) * 2.0)
        for i, w in enumerate(weights, start=1):
            postcode_rows.append({
                "month_key": row["month_key"],
                "postcode": f"S{region_id:02d}{i:02d}",
                "region_id": region_id,
                "inbound_volume": int(round(total * w)),
            })
    fact_postcode = pd.DataFrame(postcode_rows)

    frames = {
        **dims,
        "fact_parcel_od_daily": fact_od,
        "fact_daily_demand": fact_daily,
        "fact_postcode_volume_monthly": fact_postcode,
    }
    paths: dict[str, Path] = {}
    for name, df in frames.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        paths[name] = path
    return paths
