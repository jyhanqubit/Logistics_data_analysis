# AGENTS.md — ParcelFlow AI PoC

이 레포지토리는 물류 데이터분석가 포트폴리오용 PoC입니다. Codex는 아래 규칙을 지켜 작업합니다.

## 프로젝트 목표

공개 생활물류 데이터 또는 공개데이터형 샘플 데이터를 기반으로 다음 파이프라인을 구현합니다.

1. 데이터 수집/정제/DB 구축
2. SCM KPI 및 OD 흐름 분석
3. 지역·상품군별 수요예측
4. 마이크로 풀필먼트/택배락커 후보지 추천
5. 배송경로 및 QUBO 기반 최적화 실험
6. 대시보드와 포트폴리오 리포트 생성

## 개발 규칙

- 모든 Python 패키지 코드는 `src/parcelflow/` 아래에 둔다.
- 실행 스크립트는 `scripts/` 아래에 둔다.
- 대시보드 코드는 `dashboard/` 아래에 둔다.
- DB DDL은 `db/schema.sql`에 유지한다.
- 산출물은 `outputs/`에 생성하되, 대용량 파일은 Git에 올리지 않는다.
- 테스트는 `tests/` 아래에 작성한다.
- 공개데이터 출처와 라이선스/제약은 `docs/public_data_sources.md`에 기록한다.
- 수요예측 모델은 반드시 baseline과 비교한다.
- 추천 시스템은 추천 사유를 함께 제공한다.
- 최적화 모듈은 OR-Tools 또는 classical heuristic baseline과 QUBO/quantum-ready formulation을 비교한다.
- 합성 데이터와 실제 공개데이터를 명확히 구분한다.
- 실제 CJ대한통운 내부 데이터로 오해될 표현을 금지한다.

## 코드 품질 기준

- 함수에는 타입 힌트를 가능한 한 추가한다.
- 랜덤성은 seed를 고정한다.
- SQL 쿼리는 읽기 쉽게 작성한다.
- 모델 평가는 train/test temporal split 기준으로 수행한다.
- 오류 메시지는 사용자가 다음 행동을 알 수 있게 작성한다.

## Codex에게 추천하는 작업 순서

1. `.codex/prompts/01_data_engineering.md`
2. `.codex/prompts/02_scm_analysis.md`
3. `.codex/prompts/03_forecasting.md`
4. `.codex/prompts/04_recommender.md`
5. `.codex/prompts/05_optimization_quantum.md`
6. `.codex/prompts/06_review_and_packaging.md`
