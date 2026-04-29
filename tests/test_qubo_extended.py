from __future__ import annotations

from pathlib import Path
import pandas as pd

from parcelflow.advanced_analytics.qubo_extended import run_qubo_extended


def test_qubo_extended_shapes(tmp_path: Path) -> None:
    rec = pd.DataFrame({"region_name": [f"R{i}" for i in range(12)], "score": list(range(12, 0, -1))})
    scm = pd.DataFrame({"region_name": [f"S{i}" for i in range(5)], "total_volume": [100, 90, 80, 70, 60]})
    run_qubo_extended(rec, scm, tmp_path)
    q = pd.read_csv(tmp_path / "qubo_matrix_extended.csv")
    e = pd.read_csv(tmp_path / "qubo_eigenvalues.csv")
    n = len(q)
    assert len(e) == n
