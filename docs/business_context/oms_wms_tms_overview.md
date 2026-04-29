# OMS/WMS/TMS Overview for ParcelFlow AI

> 본 프로젝트는 **공개 생활물류/택배 물동량 데이터**를 기반으로 분석하며, OMS/WMS/TMS 이벤트는 운영 이해를 위한 **simulation layer**입니다. 실제 CJ대한통운 내부 원천 시스템 데이터가 아닙니다.

## OMS (Order Management System)
- 주문 접수/유효성 검증
- 주문 상태 추적 (접수, 출고지시, 취소, 반품 요청)
- 출고 지시(Release to WMS)
- 취소/반품 정책 반영

### ParcelFlow AI에서의 표현
- 공개 물동량의 지역·카테고리 수요를 주문 헤더/라인으로 시뮬레이션
- 주문상태 이벤트를 생성해 리드타임, 취소율, 피크 주문 비율 KPI 계산

## WMS (Warehouse Management System)
- 입고/재고 스냅샷 관리
- 피킹/패킹 작업 지시 및 처리
- 출고 확정

### ParcelFlow AI에서의 표현
- 주문라인 기반 재고 스냅샷, 피킹/패킹 이벤트 시뮬레이션
- 재고회전율, 피킹 생산성, stockout risk를 KPI로 계산

## TMS (Transportation Management System)
- 배차 및 운송 계획
- 경로계획/운송실행
- 배송상태 추적, SLA 관리
- 운송비 관리

### ParcelFlow AI에서의 표현
- 주문을 shipment로 변환하고 배송 이벤트(픽업/배송완료) 시뮬레이션
- SLA 준수율, 거리, 건당비용, 지연 리스크를 KPI로 계산

## 공개데이터 vs Simulation Layer
- 공개데이터: 지역·상품군·날짜 단위 집계 물동량
- simulation layer: 운영 이벤트 단위(주문/라인/피킹/배송) 테이블
- 목적: 실제 운영 시스템 이해도와 분석 사고를 포트폴리오로 설명하기 위함
