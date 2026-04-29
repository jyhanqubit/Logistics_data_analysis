from __future__ import annotations

import importlib.util
from pathlib import Path


def test_dashboard_importable() -> None:
    app_path = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    spec = importlib.util.spec_from_file_location("dashboard_app", app_path)
    assert spec is not None
