# Logistics KPI Dictionary (OMS/WMS/TMS)

> KPI는 공개 물동량 기반 simulation layer에서 계산된 포트폴리오용 지표입니다.

## OMS KPI
- `order_count`: 주문 건수
- `order_to_release_lead_time`: 주문접수~출고지시 평균 리드타임(시간)
- `cancellation_rate`: 주문 취소율
- `backorder_rate`: 재고부족으로 즉시출고 불가 비율
- `peak_order_ratio`: 전체 주문 중 최대 피크일 비중

## WMS KPI
- `inventory_turnover`: 재고회전율
- `stockout_risk_score`: 재고부족 리스크 점수
- `picking_productivity`: 시간당 피킹 처리 생산성
- `warehouse_utilization`: 창고/로케이션 활용률
- `pick_pack_cycle_time`: 피킹~패킹 평균 사이클 타임(초)

## TMS KPI
- `on_time_delivery_rate`: SLA 내 배송 비율
- `vehicle_utilization`: 차량/용량 활용률 지표
- `route_distance`: 총 운행 거리(km)
- `cost_per_delivery`: 건당 배송비
- `late_delivery_risk_score`: 지연 리스크 점수(1 - 정시배송률)
