# Data Dictionary

## dim_region

| column | description |
|---|---|
| region_id | 자치구 ID |
| region_name | 자치구명 |
| lat, lon | 자치구 중심 좌표 |
| population | 인구 규모 |
| ecommerce_index | 합성 이커머스 수요 지수 |
| income_index | 합성 소득/구매력 지수 |

## dim_category

| column | description |
|---|---|
| category_id | 상품 대분류 ID |
| category_name | 상품 대분류명 |
| perishability_score | 신선/부패 민감도 |
| bulky_score | 부피/중량 민감도 |

## fact_daily_demand

| column | description |
|---|---|
| date_key | 일자 |
| dest_region_id | 도착 자치구 ID |
| category_id | 상품 대분류 ID |
| inbound_volume | 도착 물동량 |

## fact_parcel_od_daily

| column | description |
|---|---|
| date_key | 일자 |
| origin_region_id | 출발 자치구 ID |
| dest_region_id | 도착 자치구 ID |
| category_id | 상품 대분류 ID |
| parcel_volume | OD 물동량 |
| avg_distance_km | 평균 거리 |
| promised_sla_hours | 약속 SLA 시간 |
| simulated_delay_rate | 합성 지연율 |

## fact_postcode_volume_monthly

| column | description |
|---|---|
| month_key | 월 |
| postcode | 합성 우편번호 |
| region_id | 자치구 ID |
| inbound_volume | 월별 도착 물동량 |
