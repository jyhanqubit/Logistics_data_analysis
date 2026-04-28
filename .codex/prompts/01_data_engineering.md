# Task: Data Engineering

AGENTS.md를 먼저 읽으세요.

목표: 실제 공개데이터 CSV를 `data/raw/external/`에서 읽어 `fact_daily_demand`, `fact_parcel_od_daily`, `fact_postcode_volume_monthly`로 정규화하는 ingestion adapter를 구현하세요.

요구사항:

1. `src/parcelflow/ingestion_external.py`에 실제 컬럼 매핑 함수를 추가합니다.
2. 입력 CSV 컬럼이 다를 경우 친절한 오류 메시지와 매핑 가이드를 제공합니다.
3. synthetic pipeline은 깨지면 안 됩니다.
4. `docs/data_dictionary.md`와 `docs/public_data_sources.md`를 업데이트합니다.
5. smoke test를 추가합니다.
