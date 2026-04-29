from __future__ import annotations

import os
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd


def run_qubo_extended(recommender_df: pd.DataFrame, scm_df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    n_req = int(os.getenv("QUBO_NUM_CANDIDATES", "10"))
    k = int(os.getenv("QUBO_SELECT_K", "3"))

    cand = pd.DataFrame()
    if not recommender_df.empty and "region_name" in recommender_df.columns:
        cand = recommender_df.sort_values("score", ascending=False).drop_duplicates("region_name")
        cand = cand[["region_name", "score"]].rename(columns={"score": "benefit_score"})
    if cand.empty and not scm_df.empty and "region_name" in scm_df.columns:
        base_col = "total_volume" if "total_volume" in scm_df.columns else scm_df.columns[1]
        cand = scm_df.sort_values(base_col, ascending=False)[["region_name", base_col]].rename(columns={base_col: "benefit_score"})

    if cand.empty:
        cand = pd.DataFrame({"region_name": [f"C{i}" for i in range(1, n_req + 1)], "benefit_score": np.linspace(1, 0.2, n_req)})

    cand = cand.head(n_req).copy()
    n = len(cand)
    k = min(max(1, k), n)

    rng = np.random.default_rng(42)
    fixed = rng.uniform(0.1, 1.0, n)
    overlap = rng.uniform(0, 0.3, (n, n))
    overlap = (overlap + overlap.T) / 2
    np.fill_diagonal(overlap, 0)

    lam, mu, gamma = 2.0, 1.0, 0.4
    Q = np.zeros((n, n))
    b = cand["benefit_score"].to_numpy(dtype=float)
    for i in range(n):
        Q[i, i] += -b[i] + gamma * fixed[i] + lam * (1 - 2 * k)
    for i in range(n):
        for j in range(i + 1, n):
            Q[i, j] += 2 * lam + mu * overlap[i, j]
            Q[j, i] = Q[i, j]

    solutions = []
    if n <= 20:
        for bits in product([0, 1], repeat=n):
            x = np.array(bits)
            if int(x.sum()) != k:
                continue
            e = float(x @ Q @ x)
            selected = [cand.iloc[i]["region_name"] for i, b in enumerate(bits) if b == 1]
            solutions.append(
                {
                    "bitstring": "".join(map(str, bits)),
                    "selected_count": int(x.sum()),
                    "energy": e,
                    "selected_candidates": ", ".join(selected),
                    "is_feasible_select_k": bool(int(x.sum()) == k),
                }
            )
    else:
        x = np.zeros(n)
        top = np.argsort(-b)[:k]
        x[top] = 1
        selected = [cand.iloc[i]["region_name"] for i, b in enumerate(x.astype(int)) if b == 1]
        solutions.append(
            {
                "bitstring": "".join(map(str, x.astype(int))),
                "selected_count": int(x.sum()),
                "energy": float(x @ Q @ x),
                "selected_candidates": ", ".join(selected),
                "is_feasible_select_k": bool(int(x.sum()) == k),
            }
        )

    sdf = pd.DataFrame(solutions).sort_values("energy").head(10).reset_index(drop=True)
    sdf["rank"] = np.arange(1, len(sdf) + 1)
    evals = np.linalg.eigvals(Q)
    edf = pd.DataFrame({"eigenvalue_index": np.arange(len(evals)), "eigenvalue": evals.real, "abs_eigenvalue": np.abs(evals.real), "sign": np.sign(evals.real)})

    qmat = pd.DataFrame(Q, columns=[f"x{i}" for i in range(n)])
    qmat.insert(0, "var", [f"x{i}" for i in range(n)])

    cand["fixed_cost_score"] = fixed
    cand["distance_penalty"] = rng.uniform(0, 1, len(cand))
    cand["overlap_penalty"] = overlap.sum(axis=1)
    cand["select_k_penalty"] = lam

    matrix_path = out_dir / "qubo_matrix_extended.csv"
    sol_path = out_dir / "qubo_solution_extended.csv"
    eig_path = out_dir / "qubo_eigenvalues.csv"
    cand_path = out_dir / "qubo_candidates.csv"
    summary_path = out_dir / "qubo_extended_summary.md"

    qmat.to_csv(matrix_path, index=False, encoding="utf-8-sig")
    sdf.to_csv(sol_path, index=False, encoding="utf-8-sig")
    edf.to_csv(eig_path, index=False, encoding="utf-8-sig")
    cand.to_csv(cand_path, index=False, encoding="utf-8-sig")
    summary_path.write_text(f"# QUBO Extended Summary\n\nCandidate n={n}, selected K={k}.\n", encoding="utf-8")

    return {"matrix": matrix_path, "solution": sol_path, "eigenvalues": eig_path, "candidates": cand_path, "summary": summary_path}
