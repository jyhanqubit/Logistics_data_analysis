from __future__ import annotations

from pathlib import Path

import pandas as pd

from .db import query_df


def run_scm_analysis(db_path: Path, output_dir: Path) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)

    top_od_lanes = query_df(db_path, """
        SELECT
            o.region_name AS origin_region,
            d.region_name AS dest_region,
            c.category_name,
            SUM(f.parcel_volume) AS total_volume,
            ROUND(AVG(f.avg_distance_km), 2) AS avg_distance_km,
            ROUND(AVG(f.simulated_delay_rate), 4) AS avg_delay_rate
        FROM fact_parcel_od_daily f
        JOIN dim_region o ON f.origin_region_id = o.region_id
        JOIN dim_region d ON f.dest_region_id = d.region_id
        JOIN dim_category c ON f.category_id = c.category_id
        GROUP BY 1, 2, 3
        ORDER BY total_volume DESC
        LIMIT 50
    """)

    region_daily_volume = query_df(db_path, """
        SELECT
            f.date_key,
            r.region_name,
            SUM(f.inbound_volume) AS inbound_volume
        FROM fact_daily_demand f
        JOIN dim_region r ON f.dest_region_id = r.region_id
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    category_daily_volume = query_df(db_path, """
        SELECT
            f.date_key,
            c.category_name,
            SUM(f.inbound_volume) AS inbound_volume
        FROM fact_daily_demand f
        JOIN dim_category c ON f.category_id = c.category_id
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)

    region_volatility = query_df(db_path, """
        WITH region_daily AS (
            SELECT dest_region_id, date_key, SUM(inbound_volume) AS daily_volume
            FROM fact_daily_demand
            GROUP BY dest_region_id, date_key
        )
        SELECT
            r.region_name,
            ROUND(AVG(rd.daily_volume), 2) AS avg_daily_volume,
            ROUND(SUM(rd.daily_volume), 0) AS total_volume,
            ROUND(
                (AVG(rd.daily_volume * rd.daily_volume) - AVG(rd.daily_volume) * AVG(rd.daily_volume)),
                2
            ) AS variance_proxy
        FROM region_daily rd
        JOIN dim_region r ON rd.dest_region_id = r.region_id
        GROUP BY r.region_name
        ORDER BY total_volume DESC
    """)
    # SQLite에는 STDDEV가 없으므로 pandas에서 CV 계산
    tmp = region_daily_volume.groupby("region_name")["inbound_volume"].agg(["mean", "std", "sum"]).reset_index()
    tmp["cv"] = (tmp["std"] / tmp["mean"]).round(4)
    tmp = tmp.rename(columns={"mean": "avg_daily_volume", "std": "std_daily_volume", "sum": "total_volume"})
    region_volatility = tmp.sort_values("total_volume", ascending=False)

    hub_load = query_df(db_path, """
        WITH demand AS (
            SELECT dest_region_id, SUM(inbound_volume) AS volume
            FROM fact_daily_demand
            GROUP BY dest_region_id
        ), hub_distance AS (
            SELECT
                h.hub_id,
                h.hub_name,
                h.capacity_daily,
                r.region_id,
                r.region_name,
                ABS(h.lat - r.lat) + ABS(h.lon - r.lon) AS manhattan_geo_distance,
                d.volume
            FROM dim_hub_candidate h
            CROSS JOIN dim_region r
            JOIN demand d ON r.region_id = d.dest_region_id
        ), nearest AS (
            SELECT *
            FROM hub_distance hd
            WHERE hd.manhattan_geo_distance = (
                SELECT MIN(hd2.manhattan_geo_distance)
                FROM hub_distance hd2
                WHERE hd2.region_id = hd.region_id
            )
        )
        SELECT
            hub_name,
            capacity_daily,
            ROUND(SUM(volume) / (SELECT COUNT(DISTINCT date_key) FROM fact_daily_demand), 0) AS assigned_avg_daily_volume,
            ROUND((SUM(volume) / (SELECT COUNT(DISTINCT date_key) FROM fact_daily_demand)) / capacity_daily, 4) AS simulated_utilization
        FROM nearest
        GROUP BY hub_name, capacity_daily
        ORDER BY simulated_utilization DESC
    """)

    outputs = {
        "top_od_lanes": top_od_lanes,
        "region_daily_volume": region_daily_volume,
        "category_daily_volume": category_daily_volume,
        "region_volatility": region_volatility,
        "hub_load_simulation": hub_load,
    }
    for name, df in outputs.items():
        df.to_csv(output_dir / f"{name}.csv", index=False, encoding="utf-8-sig")

    if region_volatility.empty or top_od_lanes.empty or hub_load.empty:
        summary = """
# SCM 분석 요약

## 핵심 발견

- 분석 대상 데이터가 비어 있어 상세 KPI를 계산하지 못했습니다.

## 다음 확인 항목

1. `fact_daily_demand`, `fact_parcel_od_daily`에 적재된 행 수를 확인하세요.
2. 서울 raw 파일의 지역/카테고리 컬럼이 표준 스키마로 매핑되었는지 확인하세요.
3. 매핑 후 `dropna`로 제거된 행이 과도한지 확인하세요.
""".lstrip()
        (output_dir / "scm_summary.md").write_text(summary, encoding="utf-8")
        return outputs

    top_region = region_volatility.iloc[0]
    top_lane = top_od_lanes.iloc[0]
    highest_util = hub_load.iloc[0]
    summary = f"""
# SCM 분석 요약

## 핵심 발견

- 총 물동량 1위 지역: **{top_region['region_name']}** / 총 {int(top_region['total_volume']):,}건
- 최상위 OD lane: **{top_lane['origin_region']} → {top_lane['dest_region']} / {top_lane['category_name']}** / 총 {int(top_lane['total_volume']):,}건
- 부하율이 가장 높은 가상 허브: **{highest_util['hub_name']}** / 평균 일 {int(highest_util['assigned_avg_daily_volume']):,}건 / 부하율 {float(highest_util['simulated_utilization']):.2%}

## 해석

이 결과는 공개데이터형 합성 데이터 기준입니다. 실제 서울 생활물류 데이터 연결 시 동일한 쿼리 구조로 자치구별 수요 집중도, OD 흐름, 허브 부하율을 산출할 수 있습니다.
""".lstrip()
    (output_dir / "scm_summary.md").write_text(summary, encoding="utf-8")
    return outputs
