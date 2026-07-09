# 수요예측 요약 (rolling-origin backtest)

## 평가 설계
- Expanding-window rolling-origin, 3 folds x 28일 horizon
- 테스트 구간은 recursive multi-step 예측 (예측값을 lag로 되먹임, 실측 미사용)
- Baseline: seasonal naive (origin 이전 마지막 동일 요일 실측 반복)

## 결과
- 모델(recursive) WAPE: 평균 **11.68%** (fold별 15.77%, 11.77%, 7.50%)
- Naive WAPE: 평균 **10.47%**
- 운영 예측(h<= 14일 모델, 이후 naive 전환) WAPE: 평균 **9.55%**
- 운영 예측의 naive 대비 개선: **8.7%**

단일 holdout에 테스트 구간 실측 lag를 넣고 평가하면 WAPE가 6% 수준으로 나오지만,
이는 1-step 성능을 28일 성능처럼 부풀리는 누수다. 위 수치가 운영 조건의 성능이며,
모델 단독은 장기 horizon에서 naive에 지기 때문에 전환 정책을 함께 쓴다.

## Horizon별 WAPE (fold 평균)
horizon  wape_model  wape_naive
 h01-07      0.0731      0.1024
 h08-14      0.0949      0.1017
 h15-28      0.1505      0.1073

Horizon이 길수록 recursive 오차가 누적돼 WAPE가 상승하는 것이 정상이며, 이 수치가
운영에서 기대할 수 있는 실제 다중일 예측 성능이다.

## Quantile 예측 (최종 28일 구간 empirical coverage)
q10: 18.8%, q50: 70.5%, q75: 87.0%, q90: 95.6%

Quantile 예측은 용량 배분(newsvendor) 레이어의 입력으로 쓰인다. Coverage가 목표
수준과 크게 어긋나면 quantile 보정(conformal 등)을 검토한다.
