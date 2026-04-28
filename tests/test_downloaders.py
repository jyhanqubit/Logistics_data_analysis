from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parcelflow.downloaders import download_public_data
from parcelflow.downloaders.seoul_open_data import SeoulOpenDataClient


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def test_seoul_open_data_pagination(monkeypatch: pytest.MonkeyPatch) -> None:
    service = "SVC"
    payloads = [
        {service: {"RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"}, "list_total_count": 1500, "row": [{"id": i} for i in range(1000)]}},
        {service: {"RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"}, "list_total_count": 1500, "row": [{"id": i} for i in range(1000, 1500)]}},
    ]

    def fake_get(url: str, **kwargs):
        return _FakeResponse(payloads.pop(0))

    monkeypatch.setattr("parcelflow.downloaders.seoul_open_data.safe_request_get", fake_get)
    df = SeoulOpenDataClient(api_key="k").fetch_service_rows(service)
    assert len(df) == 1500


def test_seoul_open_data_with_extra_path_segment(monkeypatch: pytest.MonkeyPatch) -> None:
    service = "SVC"
    captured_urls: list[str] = []

    def fake_get(url: str, **kwargs):
        captured_urls.append(url)
        return _FakeResponse({service: {"RESULT": {"CODE": "INFO-000", "MESSAGE": "OK"}, "list_total_count": 1, "row": [{"id": 1}]}})

    monkeypatch.setattr("parcelflow.downloaders.seoul_open_data.safe_request_get", fake_get)
    SeoulOpenDataClient(api_key="k").fetch_service_rows(service, extra_path_segments=["20180101"])
    assert captured_urls[0].endswith("/json/SVC/1/1000/20180101/")


def test_seoul_open_data_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SEOUL_OPEN_API_KEY", raising=False)
    with pytest.raises(ValueError):
        SeoulOpenDataClient(api_key=None).fetch_service_rows("SVC")


def test_download_public_data_graceful_skip_without_keys(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SEOUL_OPEN_API_KEY", raising=False)
    monkeypatch.delenv("SEOUL_LOGISTICS_SERVICE_NAME", raising=False)
    monkeypatch.delenv("DATA_GO_KR_SERVICE_KEY", raising=False)
    monkeypatch.delenv("DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT", raising=False)
    monkeypatch.setenv("SEOUL_PROGRESS_EVERY", "1")

    outputs = download_public_data(tmp_path)
    assert outputs["seoul_logistics"] is not None
    assert outputs["postcode_volume"] is not None

    seoul_df = pd.read_csv(outputs["seoul_logistics"])
    postcode_df = pd.read_csv(outputs["postcode_volume"])
    assert not seoul_df.empty
    assert {"month_key", "postcode", "inbound_volume"}.issubset(postcode_df.columns)


def test_download_public_data_date_range_calls_daily(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("SEOUL_OPEN_API_KEY", "k")
    monkeypatch.setenv("SEOUL_LOGISTICS_SERVICE_NAME", "SVC")
    monkeypatch.setenv("SEOUL_DLVR_YMD_START", "20180101")
    monkeypatch.setenv("SEOUL_DLVR_YMD_END", "20180103")
    monkeypatch.delenv("DATA_GO_KR_POSTCODE_VOLUME_ENDPOINT", raising=False)
    monkeypatch.setenv("SEOUL_PROGRESS_EVERY", "1")

    called_dates: list[str] = []

    def fake_fetch(self, service_name: str, page_size: int = 1000, *, extra_path_segments: list[str] | None = None):
        if extra_path_segments:
            called_dates.append(extra_path_segments[0])
        return pd.DataFrame(
            [
                {
                    "DLVR_YMD": extra_path_segments[0] if extra_path_segments else "20180101",
                    "ORIGIN_REGION": "강남구",
                    "DEST_REGION": "마포구",
                    "CATEGORY": "생활용품",
                    "PARCEL_VOLUME": 10,
                }
            ]
        )

    monkeypatch.setattr("parcelflow.downloaders.seoul_open_data.SeoulOpenDataClient.fetch_service_rows", fake_fetch)

    outputs = download_public_data(tmp_path)
    assert outputs["seoul_logistics"] is not None
    assert called_dates == ["20180101", "20180102", "20180103"]
    out = capsys.readouterr().out
    assert "Seoul API progress 1/3" in out
    assert "Seoul API progress 3/3" in out
