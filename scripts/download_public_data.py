from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from parcelflow.downloaders import download_public_data


def main() -> None:
    outputs = download_public_data(ROOT)
    for key, path in outputs.items():
        if path is None:
            print(f"[SKIP] {key}: no file produced")
        else:
            print(f"[OK] {key}: {path}")


if __name__ == "__main__":
    main()
