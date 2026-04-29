from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 2 or len(b) < 2:
        return np.nan
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    pooled = np.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / max(1, len(a) + len(b) - 2))
    return float((np.mean(a) - np.mean(b)) / pooled) if pooled else np.nan


def run_statistical_tests(feature_df: pd.DataFrame, out_dir: Path, alpha: float = 0.05) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = feature_df.copy()
    peak = df[df["is_peak_season"] == 1]["inbound_volume"].to_numpy()
    non_peak = df[df["is_peak_season"] == 0]["inbound_volume"].to_numpy()

    rows = []
    summary = []

    t_stat, t_p = stats.ttest_ind(peak, non_peak, equal_var=False) if len(peak) > 1 and len(non_peak) > 1 else (np.nan, np.nan)
    rows.append({
        "test_id": "T001",
        "business_question": "피크 시즌과 비피크 시즌 평균 물동량 차이",
        "test_name": "Welch t-test",
        "group_a": "peak",
        "group_b": "non_peak",
        "statistic": t_stat,
        "p_value": t_p,
        "alpha": alpha,
        "reject_null": bool(t_p < alpha) if not np.isnan(t_p) else False,
        "effect_size": _cohens_d(peak, non_peak),
        "interpretation": "유의하면 피크 시즌 운영 분리전략 필요",
        "business_action": "피크 시즌 안전재고/인력 선증설",
    })

    if len(peak) > 2 and len(non_peak) > 2:
        lev_stat, lev_p = stats.levene(peak, non_peak)
        rows.append({
            "test_id": "T002",
            "business_question": "피크/비피크 분산 동일성",
            "test_name": "Levene",
            "group_a": "peak",
            "group_b": "non_peak",
            "statistic": lev_stat,
            "p_value": lev_p,
            "alpha": alpha,
            "reject_null": bool(lev_p < alpha),
            "effect_size": np.nan,
            "interpretation": "유의하면 변동성 관리 필요",
            "business_action": "가변 인력 운영",
        })

    sdf = pd.DataFrame(rows)
    edf = sdf[["test_id", "effect_size"]].copy()
    gdf = pd.DataFrame(
        {
            "group": ["peak", "non_peak"],
            "mean": [np.mean(peak) if len(peak) else np.nan, np.mean(non_peak) if len(non_peak) else np.nan],
            "std": [np.std(peak) if len(peak) else np.nan, np.std(non_peak) if len(non_peak) else np.nan],
            "count": [len(peak), len(non_peak)],
        }
    )

    tests_path = out_dir / "statistical_tests.csv"
    effect_path = out_dir / "effect_sizes.csv"
    group_path = out_dir / "group_summary.csv"
    summary_path = out_dir / "statistics_summary.md"

    sdf.to_csv(tests_path, index=False, encoding="utf-8-sig")
    edf.to_csv(effect_path, index=False, encoding="utf-8-sig")
    gdf.to_csv(group_path, index=False, encoding="utf-8-sig")
    summary_path.write_text("# Statistical Tests Summary\n\np-value와 effect size를 함께 해석합니다.\n", encoding="utf-8")

    return {"tests": tests_path, "effect_sizes": effect_path, "group_summary": group_path, "summary": summary_path}
