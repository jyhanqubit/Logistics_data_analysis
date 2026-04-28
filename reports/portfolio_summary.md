# ParcelFlow AI Portfolio Summary

## 프로젝트 한 줄 설명

공개데이터형 생활물류 데이터를 기반으로 `DB 구축 → SCM 분석 → 수요예측 → 후보지 추천 → 배송/거점 최적화`를 하나의 실행 가능한 PoC로 구현했습니다.

## 데이터/DB

- SQLite PoC DB: `data/parcelflow.sqlite`
- 주요 fact row count:
  - `fact_parcel_od_daily`: 104,704
  - `fact_daily_demand`: 26,250
  - `fact_postcode_volume_monthly`: 700

## 수요예측 결과

| Model | MAE | RMSE | WAPE | sMAPE |
|---|---:|---:|---:|---:|
| Seasonal naive lag7 | 16.2149 | 21.7176 | 0.0755 | 0.0930 |
| Gradient Boosting | 13.9292 | 18.7440 | 0.0648 | 0.0788 |

## 추천 결과

- MFC 1순위: **강남구** / score 0.7772 / 예측 물동량 상위권; 최근 수요 증가율 높음; 이커머스 지수 높음
- 택배락커 1순위: **송파구** / score 0.9082 / 예측 물동량 상위권; 최근 수요 증가율 높음; 이커머스 지수 높음

## 최적화 결과

- CVRP heuristic 차량 수: 3대
- 총 route distance: 142.96 km
- QUBO best bitstring: `10100`
- QUBO selected hubs: **서북권 MFC 후보, 동남권 MFC 후보**

## 채용용 표현 예시

> 공개 생활물류 데이터를 모사한 데이터셋으로 자치구·상품군별 물동량 DB를 구축하고, SCM KPI 분석·수요예측·거점/락커 후보지 추천·배송경로 및 QUBO 기반 최적화 PoC를 구현했습니다. 모델은 seasonal naive baseline 대비 Gradient Boosting의 WAPE 개선을 검증했고, 추천 결과는 예측 물동량·성장률·허브 거리 gap 기반 설명을 함께 제공했습니다.
