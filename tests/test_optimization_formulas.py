from __future__ import annotations

from pathlib import Path

from parcelflow.advanced_analytics.optimization_formulas import generate_optimization_formulation


def test_optimization_formula_files(tmp_path: Path) -> None:
    out = generate_optimization_formulation(tmp_path)
    assert out["formulation"].exists()
    assert out["solver_comparison"].exists()
