# Public Data Sources to Connect

이 PoC는 기본적으로 합성 데이터를 사용합니다. 실제 포트폴리오 고도화 시 아래 데이터원을 연결할 수 있습니다.

## 1. 서울 열린데이터광장 생활물류 데이터

- 용도: 서울 자치구/상품군/OD 기반 생활물류 흐름 분석
- Open API 형식: `http://openapi.seoul.go.kr:8088/{KEY}/json/{SERVICE}/{START}/{END}/`
- 연결 위치: `data/raw/seoul_logistics/seoul_logistics_api.csv`
- 정규화 목표: `date_key`, `origin_region_name`, `dest_region_name`, `category_name`, `parcel_volume`
- 설정값:
  - `SEOUL_OPEN_API_KEY`
  - `SEOUL_LOGISTICS_SERVICE_NAME`
  - `SEOUL_DLVR_YMD_START` / `SEOUL_DLVR_YMD_END` (예: 20180101~20231231)

## 2. 서울 생활물류 월별 CSV fallback

- API service name이 확인되지 않은 경우를 대비해 월별 CSV 다운로드 URL 주입 방식 지원
- 설정값: `SEOUL_LOGISTICS_MONTHLY_CSV_URLS` (쉼표로 여러 URL 전달)
- 한계: 공식 페이지의 링크 구조 변경 시 자동화가 깨질 수 있어 URL 목록 업데이트가 필요

## 3. 공공데이터포털 우편번호별 택배물량

- 용도: 우편번호 단위 수요 집중도 및 락커 후보지 추천
- 연결 위치: `data/raw/postcode_volume/postcode_parcel_volume_api.csv`
- 정규화 목표: `month_key`, `postcode`, `inbound_volume`
- 설정값:
  - `DATA_GO_KR_SERVICE_KEY`
  - `DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT`
- 참고: Encoding/Decoding 키 이슈 대응을 위해 `serviceKey` 파라미터/Raw query string 방식 모두 지원

## 4. 국가물류통합정보센터 택배 통계

- 용도: 시장 규모, 월별/연도별 택배 물동량, 매출액, 단가 배경 지표

## 5. DART/CJ대한통운 사업보고서

- 용도: 사업부문, 매출, 시장 설명 등 포트폴리오 배경 정보

## 데이터 사용 주의

- 공개데이터 라이선스와 출처를 README/report에 명시합니다.
- 특정 회사 내부 운영 데이터로 오해될 표현을 피합니다.
- 통계성/집계성 데이터의 범위와 한계를 명확히 씁니다.
