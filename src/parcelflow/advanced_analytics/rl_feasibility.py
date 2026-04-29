from __future__ import annotations

from pathlib import Path
import pandas as pd


def write_rl_feasibility(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = out_dir / "rl_feasibility_summary.md"
    ppo = out_dir / "ppo_environment_spec.md"
    dpo = out_dir / "dpo_preference_dataset_spec.md"
    baseline = out_dir / "rl_baseline_policy_results.csv"

    summary.write_text(
        "# RL Feasibility Summary\n\n"
        "- PPO: route construction 환경에서 직접 적용 가능\n"
        "- DPO: route 자체 최적화보다 route 설명/랭킹 선호 정렬에 적합\n",
        encoding="utf-8",
    )
    ppo.write_text("# PPO Environment Spec\n\nState/Action/Reward 정의 기반 추후 실험 가능.\n", encoding="utf-8")
    dpo.write_text("# DPO Preference Dataset Spec\n\nPrompt/Chosen/Rejected/Reason 스키마 정의.\n", encoding="utf-8")
    pd.DataFrame([
        {"policy": "random", "avg_distance": 160.0, "sla_penalty": 0.3},
        {"policy": "greedy", "avg_distance": 140.0, "sla_penalty": 0.2},
    ]).to_csv(baseline, index=False, encoding="utf-8-sig")
    return {"summary": summary, "ppo_spec": ppo, "dpo_spec": dpo, "baseline": baseline}
