# Public Data Sources to Connect

이 PoC는 기본적으로 합성 데이터를 사용합니다. 실제 포트폴리오 고도화 시 아래 데이터원을 연결할 수 있습니다.

## 1. 서울 열린데이터광장 생활물류 데이터

- 용도: 서울 자치구/상품군/OD 기반 생활물류 흐름 분석
- 연결 위치: `data/raw/external/`
- 정규화 목표: `date_key`, `origin_region_name`, `dest_region_name`, `category_name`, `parcel_volume`

## 2. 공공데이터포털 우편번호별 택배물량

- 용도: 우편번호 단위 수요 집중도 및 락커 후보지 추천
- 정규화 목표: `month_key`, `postcode`, `region_id`, `inbound_volume`

## 3. 국가물류통합정보센터 택배 통계

- 용도: 시장 규모, 월별/연도별 택배 물동량, 매출액, 단가 배경 지표

## 4. DART/CJ대한통운 사업보고서

- 용도: 사업부문, 매출, 시장 설명 등 포트폴리오 배경 정보

## 데이터 사용 주의

- 공개데이터 라이선스와 출처를 README/report에 명시합니다.
- 특정 회사 내부 운영 데이터로 오해될 표현을 피합니다.
- 통계성/집계성 데이터의 범위와 한계를 명확히 씁니다.
