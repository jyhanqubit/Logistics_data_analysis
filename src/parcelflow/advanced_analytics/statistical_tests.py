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

    if len(peak) > 7 and len(non_peak) > 7:
        mw_stat, mw_p = stats.mannwhitneyu(peak, non_peak, alternative="two-sided")
        rows.append({
            "test_id": "T003",
            "business_question": "피크/비피크 물동량 분포가 다른가(비모수)",
            "test_name": "Mann-Whitney U",
            "group_a": "peak",
            "group_b": "non_peak",
            "statistic": mw_stat,
            "p_value": mw_p,
            "alpha": alpha,
            "reject_null": bool(mw_p < alpha),
            "effect_size": _cohens_d(peak, non_peak),
            "interpretation": "유의하면 평균뿐 아니라 분포 자체가 달라 운영정책 분리 필요",
            "business_action": "피크 전용 배차/재고 정책 분리",
        })

    if len(peak) > 2 and len(non_peak) > 2:
        ks_stat, ks_p = stats.ks_2samp(peak, non_peak)
        rows.append({
            "test_id": "T004",
            "business_question": "피크/비피크 누적분포 형태가 다른가",
            "test_name": "Kolmogorov-Smirnov 2-sample",
            "group_a": "peak",
            "group_b": "non_peak",
            "statistic": ks_stat,
            "p_value": ks_p,
            "alpha": alpha,
            "reject_null": bool(ks_p < alpha),
            "effect_size": _cohens_d(peak, non_peak),
            "interpretation": "유의하면 특정 구간에서 극단치 대응 정책 필요",
            "business_action": "상위 분위수(예: p90 이상) 대응 룰 운영",
        })

    if len(df) > 10:
        peak_dummy = df["is_peak_season"].astype(float).to_numpy()
        vol = df["inbound_volume"].astype(float).to_numpy()
        corr, corr_p = stats.spearmanr(peak_dummy, vol)
        rows.append({
            "test_id": "T005",
            "business_question": "피크 시즌 여부와 물동량의 단조 관계가 있는가",
            "test_name": "Spearman correlation",
            "group_a": "is_peak_season",
            "group_b": "inbound_volume",
            "statistic": corr,
            "p_value": corr_p,
            "alpha": alpha,
            "reject_null": bool(corr_p < alpha) if not np.isnan(corr_p) else False,
            "effect_size": corr,
            "interpretation": "유의하면 피크 플래그 기반 사전경보 체계 유효",
            "business_action": "피크 신호 연동 사전 증설 기준 도입",
        })

    cat_col = "category_id" if "category_id" in df.columns else None
    if cat_col is not None:
        grouped = [g["inbound_volume"].to_numpy() for _, g in df.groupby(cat_col) if len(g) > 2]
        if len(grouped) >= 3:
            anova_stat, anova_p = stats.f_oneway(*grouped)
            rows.append({
                "test_id": "T006",
                "business_question": "카테고리별 평균 물동량 차이가 있는가",
                "test_name": "One-way ANOVA",
                "group_a": "category groups",
                "group_b": "inbound_volume",
                "statistic": anova_stat,
                "p_value": anova_p,
                "alpha": alpha,
                "reject_null": bool(anova_p < alpha),
                "effect_size": np.nan,
                "interpretation": "유의하면 카테고리별 SLA/재고정책 차등화 필요",
                "business_action": "카테고리군별 안전재고/리드타임 정책 분리",
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
    summary_lines = [
        "# Statistical Tests Summary",
        "",
        "- 해석 원칙: p-value와 effect size를 함께 확인합니다.",
        "- p-value < alpha 이고 effect size가 큰 항목을 우선 액션으로 연결합니다.",
        f"- 수행된 테스트 수: {len(sdf)}",
        "",
        "## Test Meaning",
        "- Welch t-test: 평균 차이 확인",
        "- Levene: 분산(변동성) 차이 확인",
        "- Mann-Whitney U: 비모수 분포 중심 차이 확인",
        "- KS 2-sample: 누적분포 형태 차이 확인",
        "- Spearman: 단조 상관 관계 확인",
        "- One-way ANOVA: 다집단 평균 차이 확인",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {"tests": tests_path, "effect_sizes": effect_path, "group_summary": group_path, "summary": summary_path}
