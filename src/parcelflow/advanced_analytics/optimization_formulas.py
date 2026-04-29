from __future__ import annotations

from pathlib import Path
import pandas as pd


def generate_optimization_formulation(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / "optimization_formulation.md"
    solver = out_dir / "solver_comparison.csv"
    summary = out_dir / "optimization_summary.md"

    md.write_text(
        "# Optimization Formulation\n\n"
        "## CVRP\n"
        "Objective: $\\min \\sum_{k\\in K}\\sum_i\\sum_{j\\neq i} d_{ij}x_{ijk}$\n\n"
        "## Facility Location\n"
        "Objective: $\\max \\sum_i\\sum_j demand_i y_{ij} - \\lambda\\sum_j cost_j z_j$\n\n"
        "## QUBO\n"
        "Objective: $\\min x^TQx$ with benefit, select-k, overlap, cost penalties.\n",
        encoding="utf-8",
    )
    pd.DataFrame([
        {"solver": "OR-Tools/Heuristic", "strength": "CVRP baseline", "priority": "High"},
        {"solver": "QUBO brute force", "strength": "Quantum-ready formulation validation", "priority": "Medium"},
    ]).to_csv(solver, index=False, encoding="utf-8-sig")
    summary.write_text("# Optimization Summary\n\nCVRP baseline + QUBO formulation 비교 결과.\n", encoding="utf-8")
    return {"formulation": md, "solver_comparison": solver, "summary": summary}
