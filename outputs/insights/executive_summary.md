# Executive Summary

공개데이터 + simulation layer 기반 의사결정 권고안입니다.

- [High] Best model=RandomForestRegressor, WAPE=0.024. 피크 구간 오차 관리가 필요합니다. -> 피크 시즌 전용 재학습과 high-error segment 수동 rule을 병행 적용하세요.
- [High] 금천구의 SLA 리스크가 상위권이며 평균 risk score=0.474입니다. -> SLA 고위험 지역 우선 배차 규칙과 임시 차량 슬롯을 배치하세요.
- [High] 송파구 locker_score=0.908로 상위권입니다. -> 상위 3개 후보지를 현장 실사 shortlist에 포함하세요.
- [Medium] 피크 주문군에서 출고지시 지연이 집중되는 패턴이 관찰됩니다. -> 피크 주간 OMS cut-off를 1시간 앞당기고 출고 wave를 추가 증설합니다.
- [Medium] 재고 커버리지 하위 SKU군에서 stockout 발생 확률이 높습니다. -> 고위험 SKU 안전재고를 20% 상향하고 리오더 트리거를 당겨 발주합니다.