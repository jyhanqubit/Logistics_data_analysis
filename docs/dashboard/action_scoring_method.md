# Action Value Scoring Method

Action value는 실행 우선순위를 정량화하기 위한 내부 점수입니다.

- `expected_impact_score` : 실행 시 기대되는 비즈니스 효과 점수 (0~1)
- `urgency_score` : 미실행 시 리스크/긴급도 점수 (0~1)
- `action_value` : 최종 우선순위 점수

공식:

```text
action_value = 0.6 * expected_impact_score + 0.4 * urgency_score
```

해석:
- 0.8 이상: 즉시 실행 권고
- 0.6~0.8: 단기 실행 후보
- 0.6 미만: 중장기 검토

주의:
- 본 점수는 공개데이터+simulation layer 기반의 의사결정 보조지표입니다.
- 특정 기업 내부 실제 KPI 임계치와 동일하지 않습니다.
