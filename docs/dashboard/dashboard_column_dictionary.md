# Dashboard Column Dictionary

## Forecasting
- `wape`, `mae`, `rmse`, `smape`: 예측 오차 지표
- `y_true`, `y_pred`: 실제/예측 수요

## Recommendation
- `score`: 추천 종합 점수
- `forecast_volume`: 예측 물동량
- `growth_rate`: 수요 성장률
- `nearest_hub_distance_km`: 기존 허브와의 거리
- `reason`: 추천 사유 텍스트

## Route Optimization
- `total_distance_km`: 총 이동거리
- `vehicle_id`: 차량 식별자

## QUBO
- `bitstring`: 후보지 선택 상태(0/1)
- `energy`: 목적함수 값 (낮을수록 유리)
- `selected_hubs`: 선택된 후보지 설명
