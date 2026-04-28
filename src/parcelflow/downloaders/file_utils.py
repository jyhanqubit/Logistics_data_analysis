from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import requests


ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp949", "euc-kr")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_dataframe_csv(df: pd.DataFrame, output_path: Path) -> Path:
    ensure_dir(output_path.parent)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def read_csv_with_encoding_fallback(path: Path, encodings: tuple[str, ...] = ENCODING_CANDIDATES) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    raise ValueError(
        f"Unable to read CSV {path} with supported encodings: {', '.join(encodings)}"
    ) from last_error


def safe_request_get(url: str, **kwargs: Any) -> requests.Response:
    timeout = kwargs.pop("timeout", 30)
    try:
        response = requests.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        raise RuntimeError(
            f"HTTP request failed for {url}. Check endpoint/auth params and try again. Details: {exc}"
        ) from exc
