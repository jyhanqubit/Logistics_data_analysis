# Codex Workflow

## 목적

Codex를 이 레포의 개발 subagent로 사용해 실제 공개데이터 연결, 모델 개선, 코드 리뷰, 대시보드 개선을 반복합니다.

## 권장 실행 방식

### 1. CLI에서 직접 실행

```bash
codex
```

요청 예시:

```text
AGENTS.md를 읽고 .codex/prompts/03_forecasting.md 요구사항대로 forecasting 모듈을 개선해줘. 단, 기존 tests가 통과해야 해.
```

### 2. MCP 서버로 실행

```bash
codex mcp-server
```

Agents SDK 또는 MCP client에서 Codex를 도구처럼 호출할 수 있습니다.

## 추천 subagent 구성

| Agent | 책임 |
|---|---|
| Data Engineer | 실제 CSV/API adapter, DB schema, data quality |
| SCM Analyst | KPI 쿼리, OD 분석, 시각화 |
| Forecasting Engineer | feature engineering, model backtest |
| Recommendation Engineer | 후보지 추천 로직, 설명 가능성 |
| Optimization Engineer | CVRP, QUBO, QAOA extension |
| Reviewer | 테스트, README, 보안/라이선스 검토 |

## Codex review checklist

- `python scripts/run_pipeline.py` 실행 성공
- `pytest` 통과
- 새로 추가한 데이터 소스의 출처/라이선스 문서화
- 합성 데이터와 실제 데이터 구분 명확화
- 모델 성능은 baseline 대비 비교
- 추천 결과는 추천 사유 포함
- 최적화 결과는 baseline과 비교
