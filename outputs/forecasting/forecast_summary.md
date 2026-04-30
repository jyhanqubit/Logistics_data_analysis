# 수요예측 요약

## 모델 비교

- Best model by WAPE: **random_forest**
- Seasonal naive WAPE: **7.55%**
- Gradient Boosting WAPE: **6.48%**
- WAPE 개선율: **14.17%**

## 해석

`지역 × 상품군 × 일자` 단위 물동량을 예측했습니다. Gradient Boosting 모델은 요일성, 월별 시즌성, 지역별 이커머스 지수, 직전 1/7/14일 lag, rolling mean을 사용합니다. 실제 공개데이터 연결 시 동일한 feature engineering과 temporal backtest 구조를 유지하면 됩니다.
