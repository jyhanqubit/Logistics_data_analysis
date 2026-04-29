# AGENTS.md — ParcelFlow AI PoC 작업 지침

## 1) 프로젝트 개요
- 이 레포는 공개 생활물류 데이터(또는 합성 데이터) 기반 물류 분석 포트폴리오 PoC입니다.
- 핵심 흐름: 데이터 준비 → DB 구축 → SCM 분석 → 수요예측 → 추천 → 최적화 → 대시보드/리포트.
- 실제 내부 기업 데이터로 오해될 표현은 금지합니다.

## 2) 주요 폴더 설명
- `src/parcelflow/`: 파이썬 패키지 코드(분석/예측/추천/최적화/시뮬레이션)
- `scripts/`: 실행 스크립트 (`run_pipeline.py`, `download_public_data.py`)
- `dashboard/`: Streamlit 대시보드 (`app.py`)
- `db/`: DB 스키마 (`schema.sql`)
- `tests/`: pytest 테스트
- `docs/`: 문서 및 데이터 출처 설명
- `outputs/`: 파이프라인 산출물
- `data/`: raw/processed/external 데이터

## 3) 실행 방법
- 가상환경/의존성 설치
  - `python -m venv .venv`
  - `source .venv/bin/activate` (Windows: `.venv\\Scripts\\activate`)
  - `pip install -r requirements.txt`
- 파이프라인 실행
  - `python scripts/run_pipeline.py`
- 대시보드 실행
  - `streamlit run dashboard/app.py`

## 4) 테스트, 린트, 타입체크 명령어
- 테스트
  - `pytest -q`
- 린트
  - 확인 필요 (현재 레포에 공식 린트 도구/설정 파일 없음)
- 타입체크
  - 확인 필요 (현재 레포에 공식 타입체크 도구/설정 파일 없음)

## 5) 코드 수정 시 지켜야 할 규칙
- 패키지 코드는 `src/parcelflow/` 아래에 둡니다.
- 실행 스크립트는 `scripts/`, 대시보드는 `dashboard/`, 테스트는 `tests/`에 둡니다.
- 랜덤성은 seed를 고정합니다.
- 함수에는 가능한 타입 힌트를 추가합니다.
- SQL은 읽기 쉽게 작성합니다.
- 오류 메시지는 다음 행동이 보이게 작성합니다.
- 합성 데이터와 공개데이터 기반 결과를 명확히 구분합니다.

## 6) 포트폴리오 품질 기준
- 예측 모델은 baseline(예: seasonal naive)과 반드시 비교합니다.
- 추천 결과에는 추천 사유(explainability)를 포함합니다.
- 최적화는 heuristic/OR-Tools baseline과 QUBO formulation 비교 관점을 유지합니다.
- 결과물은 재현 가능해야 하며(명령어/seed/출처), 데이터 한계를 문서에 명시합니다.

## 7) 작업 완료 전 반드시 확인
- 최소 1회 `pytest -q` 실행 여부
- 변경 코드와 관련된 `docs/` 업데이트 여부
- 산출물/경로/파일명 일관성(파이프라인 ↔ 대시보드 ↔ 테스트)
- 민감정보/API 키/.env/대용량 파일 미커밋 확인

## 8) 하지 말아야 할 것
- 존재하지 않는 명령어/도구를 임의로 작성하지 말 것
- 내부 실데이터를 쓴 것처럼 표현하지 말 것
- 실패를 숨기고 임의 상수로 결과를 대체한 뒤 설명 없이 넘기지 말 것
- 테스트 없이 핵심 로직 변경을 완료 처리하지 말 것
