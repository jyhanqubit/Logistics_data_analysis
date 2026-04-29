from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .file_utils import safe_request_get


SEOUL_API_BASE = "http://openapi.seoul.go.kr:8088"


@dataclass
class SeoulOpenDataClient:
    api_key: str | None = None
    base_url: str = SEOUL_API_BASE

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("SEOUL_OPEN_API_KEY", "").strip() or None

    def fetch_service_rows(
        self,
        service_name: str,
        page_size: int = 1000,
        *,
        extra_path_segments: list[str] | None = None,
    ) -> pd.DataFrame:
        if not self.api_key:
            raise ValueError(
                "SEOUL_OPEN_API_KEY is not set. Add it to environment variables before calling Seoul Open API."
            )
        if not service_name:
            raise ValueError(
                "SEOUL_LOGISTICS_SERVICE_NAME is empty. Provide service name or use CSV/synthetic fallback."
            )

        start = 1
        all_rows: list[dict[str, Any]] = []
        total_count: int | None = None
        path_tail = "/".join(extra_path_segments or [])

        while True:
            end = start + page_size - 1
            base = f"{self.base_url}/{self.api_key}/json/{service_name}/{start}/{end}"
            url = f"{base}/{path_tail}/" if path_tail else f"{base}/"
            response = safe_request_get(url)
            payload = response.json()

            service_payload = payload.get(service_name)
            if service_payload is None:
                self._raise_api_message(payload)

            result = service_payload.get("RESULT", {})
            self._raise_result_error_if_needed(result)

            rows = service_payload.get("row", [])
            all_rows.extend(rows)

            if total_count is None:
                total_count = int(service_payload.get("list_total_count", len(rows)))
            if len(all_rows) >= total_count or not rows:
                break
            start += page_size

        return pd.DataFrame(all_rows)

    @staticmethod
    def _raise_result_error_if_needed(result: dict[str, Any]) -> None:
        code = str(result.get("CODE", "")).upper()
        if code.startswith("ERROR") or code.startswith("INFO") and code not in {"INFO-000", "INFO-200"}:
            message = result.get("MESSAGE", "Unknown error from Seoul Open API")
            raise RuntimeError(
                "Seoul Open API returned a non-success result. "
                f"CODE={result.get('CODE')}, MESSAGE={message}. "
                "Check service name/range/key and retry."
            )

    def _raise_api_message(self, payload: dict[str, Any]) -> None:
        result = payload.get("RESULT", {})
        code = result.get("CODE")
        message = result.get("MESSAGE", "Unknown response format")
        if code:
            raise RuntimeError(
                "Seoul Open API response does not include requested service node. "
                f"CODE={code}, MESSAGE={message}."
            )
        raise RuntimeError(
            "Seoul Open API response shape is unexpected. Confirm service name and endpoint format."
        )
