from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlencode

import pandas as pd

from .file_utils import safe_request_get


@dataclass
class DataGoKrClient:
    service_key: str | None = None

    def __post_init__(self) -> None:
        if self.service_key is None:
            self.service_key = os.getenv("DATA_GO_KR_SERVICE_KEY", "").strip() or None

    def fetch_paginated(
        self,
        endpoint: str,
        *,
        num_of_rows: int = 1000,
        page_no_start: int = 1,
        service_key_as_query_string: bool = False,
    ) -> pd.DataFrame:
        if not self.service_key:
            raise ValueError(
                "DATA_GO_KR_SERVICE_KEY is not set. Add key to env or skip API mode with synthetic fallback."
            )

        page_no = page_no_start
        rows: list[dict] = []
        total_count: int | None = None

        while True:
            params = {
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "type": "json",
            }

            if service_key_as_query_string:
                base_query = urlencode(params)
                url = f"{endpoint}?serviceKey={self.service_key}&{base_query}"
                response = safe_request_get(url)
            else:
                params["serviceKey"] = self.service_key
                response = safe_request_get(endpoint, params=params)

            payload = response.json()
            body = (((payload.get("response") or {}).get("body")) or {})
            items_obj = body.get("items", {})
            page_rows = items_obj.get("item", []) if isinstance(items_obj, dict) else []
            if isinstance(page_rows, dict):
                page_rows = [page_rows]
            rows.extend(page_rows)

            if total_count is None:
                total_count = int(body.get("totalCount", len(page_rows)))

            if not page_rows or len(rows) >= total_count:
                break
            page_no += 1

        return pd.DataFrame(rows)


def download_postcode_parcel_volume(endpoint: str | None = None) -> pd.DataFrame:
    endpoint = (endpoint or os.getenv("DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT", "")).strip()
    if not endpoint:
        raise ValueError(
            "DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT is empty. Set endpoint to download postcode volume API data."
        )

    client = DataGoKrClient()
    try:
        return client.fetch_paginated(endpoint, service_key_as_query_string=False)
    except RuntimeError:
        return client.fetch_paginated(endpoint, service_key_as_query_string=True)
