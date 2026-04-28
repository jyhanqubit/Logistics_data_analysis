# ParcelFlow AI PoC

**생활물류 수요예측 · SCM 분석 · 거점/락커 추천 · 배송 최적화 포트폴리오 PoC**

이 레포지토리는 물류 데이터분석가 포트폴리오용으로 만든 실행 가능한 PoC입니다.  
실제 CJ대한통운 내부 데이터는 사용하지 않고, 서울 생활물류/전국 택배물량 공개데이터와 유사한 구조의 샘플 데이터를 생성해 전체 파이프라인을 검증합니다. 실제 공개 CSV/API를 확보하면 `data/raw/external/`에 넣고 동일한 DB/모델 파이프라인에 연결할 수 있도록 설계했습니다.

## 핵심 시나리오

> 지역·상품군별 생활물류 수요를 예측하고, 수요 집중 지역에 마이크로 풀필먼트 센터 또는 택배락커 설치 후보지를 추천하며, 소규모 배송 경로 최적화 및 QUBO 기반 양자 최적화 실험까지 연결한다.

## 포함 기능

| 모듈 | 산출물 |
|---|---|
| 데이터 생성/수집 | 공개데이터형 샘플 CSV, SQLite DB, SQL 스키마 |
| SCM 분석 | OD lane, 지역별 수요, 변동성, 카테고리 피크, 허브 부하 리포트 |
| 수요예측 | Gradient Boosting 기반 일별 수요 예측, baseline 비교, WAPE/MAE/RMSE/sMAPE |
| 추천 시스템 | 마이크로 풀필먼트/택배락커 후보지 랭킹 및 추천 사유 |
| 최적화 | CVRP greedy route, 2-opt 개선, QUBO hub-selection 실험 |
| Codex 연동 | `AGENTS.md`, Codex 작업 프롬프트, MCP 예시 코드 |
| 대시보드 | Streamlit 앱 예시 |

## 빠른 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_pipeline.py
```

실행 후 주요 결과물:

```text
outputs/
├── scm/
│   ├── top_od_lanes.csv
│   ├── region_daily_volume.csv
│   ├── region_volatility.csv
│   └── scm_summary.md
├── forecasting/
│   ├── forecast_predictions.csv
│   ├── model_metrics.csv
│   ├── feature_importance.csv
│   └── forecast_summary.md
├── recommender/
│   ├── site_recommendations.csv
│   └── recommendation_summary.md
└── optimization/
    ├── route_plan.csv
    ├── route_summary.md
    ├── qubo_matrix.csv
    └── qubo_solution.csv
```

## 대시보드 실행

```bash
pip install streamlit
streamlit run dashboard/app.py
```

## 실제 공개데이터 연결 아이디어

이 PoC의 기본 데이터는 샘플 생성 데이터입니다. 실제 포트폴리오에서는 다음 공개데이터를 연결하면 됩니다.

1. 서울 열린데이터광장 생활물류 데이터
2. 공공데이터포털 우편번호별 택배물량 데이터
3. 국가물류통합정보센터 택배 물동량/매출액/단가 통계
4. DART/CJ대한통운 사업보고서 기반 사업부문·시장 배경 정보

실제 CSV 연결은 `src/parcelflow/ingestion_external.py`에 확장 포인트를 남겨두었습니다.

## Codex 활용 방법

이 레포는 Codex가 바로 이해하고 작업할 수 있도록 `AGENTS.md`와 `.codex/prompts/`를 포함합니다.

예시:

```bash
codex
# 또는 MCP 서버 방식
codex mcp-server
```

Codex에게 다음처럼 요청하면 됩니다.

```text
AGENTS.md를 읽고, .codex/prompts/01_data_engineering.md의 요구사항대로 실제 서울 생활물류 CSV를 연결하는 ingestion 코드를 구현해줘.
```

## 포트폴리오 어필 포인트

이 프로젝트는 단순 EDA가 아니라 아래 역량을 동시에 보여줍니다.

- SQL/DB 모델링: fact/dim 구조, 데이터 품질 체크, 데이터 사전
- SCM 분석: OD 흐름, 수요 집중도, 변동성, 피크 분석
- ML: 시계열 피처링, baseline 비교, backtest, feature importance
- 추천 시스템: 비즈니스 점수화 + 모델 출력 기반 랭킹
- 최적화: VRP/CVRP 접근, QUBO formulation, 양자 최적화 PoC 설계
- 제품화: 대시보드, 리포트, 자동 파이프라인, Codex-ready 개발 지침

## 주의사항

- 본 PoC의 기본 데이터는 합성 데이터입니다.
- 실제 CJ대한통운 내부 운영 데이터가 아니므로 “CJ대한통운 전체 물류망 분석”으로 표현하면 안 됩니다.
- 양자 최적화 모듈은 실무 적용 엔진이 아니라 소규모 비교 실험/PoC입니다.
