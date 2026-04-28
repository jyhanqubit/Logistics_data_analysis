# ParcelFlow AI — Logistics Analytics Portfolio

## Project Overview
ParcelFlow AI는 공개 생활물류/택배 물동량 데이터를 활용해 **수요예측 PoC를 넘어 OMS/WMS/TMS 운영 분석까지** 확장한 물류 데이터 분석 포트폴리오입니다.

## Business Problem
생활물류 운영에서는 수요 변동, 재고 리스크, 배송 SLA, 거점 의사결정이 동시에 발생합니다. 이 프로젝트는 이를 하나의 데이터 파이프라인과 분석 케이스북으로 통합합니다.

## Solution Architecture
- Data ingestion (공개데이터 API/CSV + synthetic fallback)
- SCM analytics
- Forecasting (baseline 비교)
- Recommendation (거점/락커 후보지)
- Optimization (CVRP heuristic + QUBO 실험)
- OMS/WMS/TMS simulation analytics layer

## Data Sources
- 서울 열린데이터광장 생활물류 API/CSV
- 공공데이터포털 택배 물동량 API
- 합성 데이터(재현 가능한 seed 고정)

> 실제 운영 이벤트(주문/피킹/배송)는 공개 집계 데이터를 기반으로 생성한 simulation layer입니다.

## OMS/WMS/TMS Analytics Layer
`src/parcelflow/ops_simulation/`에서 다음 테이블을 생성합니다.
- orders, order_lines, inventory_snapshot, pick_pack_events
- shipments, delivery_events
- oms_kpi, wms_kpi, tms_kpi

출력 위치: `outputs/ops_simulation/`

## Analysis Casebook
`analysis_cases/`에 OMS/WMS/TMS + forecasting/recommendation/optimization 케이스를 문서화했습니다.

## Forecasting
- 일별/지역/카테고리 수요 예측
- seasonal naive baseline 대비 성능 비교

## Recommendation System
- 마이크로풀필먼트/택배락커 후보지 점수화
- 추천 사유(explainability) 제공

## Optimization
- 배송 경로 최적화(heuristic)
- QUBO 기반 거점 선택 실험

## Vector DB / Copilot Roadmap
- 운영 이벤트·KPI·케이스북을 벡터 인덱스로 연결
- 분석 질의형 Copilot 확장

## Repository Structure
- `src/parcelflow/`: 분석/모델/시뮬레이션 패키지
- `scripts/`: 실행 스크립트
- `dashboard/`: Streamlit 대시보드
- `analysis_cases/`: 포트폴리오 분석 문서
- `docs/business_context/`: OMS/WMS/TMS 업무 맥락

## How to Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_pipeline.py
pytest -q
```

## Security and Data Policy
- `.env`, API key, raw data, sqlite DB 등 민감/로컬 파일은 커밋하지 않습니다.
- 본 프로젝트는 특정 회사 내부 원천 데이터를 사용하지 않습니다.

## Portfolio Highlights
- 공개데이터 기반 End-to-End 물류 분석 파이프라인
- OMS/WMS/TMS 운영 이해를 KPI/케이스로 구조화
- 예측·추천·최적화를 하나의 비즈니스 스토리로 연결

## Advanced Analytics Modules
- Regression
- Classification
- Statistical Testing
- Time Series
- Clustering
- Optimization Formulation
- Extended QUBO
- RL / DPO / PPO Feasibility
