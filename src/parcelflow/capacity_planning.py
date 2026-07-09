from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 용량 배분 설계 노트
#
# 예측은 그 자체로 끝나지 않고 "권역별로 차량을 몇 대 배치할지"라는 결정으로
# 이어져야 한다. 이 결정은 newsvendor 구조다.
#
#   과소 배치 비용 Cu: 당일 처리 못 한 택배 1건의 페널티 (지연 배상, 재배송, 이탈)
#   과대 배치 비용 Co: 유휴 용량 1건분의 비용 (차량/기사 고정비의 낭비분)
#
# 최적 서비스 수준(critical ratio) q* = Cu / (Cu + Co).
# Cu = 1,500원/건, Co = 500원/건이면 q* = 0.75, 즉 수요분포의 75% 분위수만큼
# 용량을 준비하는 것이 기대비용 최소다. 비용은 도메인 가정이므로 상수로 분리했고,
# 실제 도입 시 현업과 함께 재추정한다.
#
# 차량 총량 제약이 있으면 권역별 독립 newsvendor로는 못 풀고 결합 최적화가 된다.
# 여기서는 quantile 예측 3점(q10/q50/q90)을 Pearson-Tukey 근사(0.3/0.4/0.3)로
# 수요 시나리오화하고, 정수 차량 대수를 결정변수로 하는 MILP를 푼다.
#
#   min  sum_r [ Co_slot * cap * n_r + sum_k p_k * Cu * s_{r,k} ]
#   s.t. s_{r,k} >= D_{r,k} - cap * n_r      (시나리오별 부족분 정의)
#        s_{r,k} >= 0
#        sum_r n_r <= F                       (보유 차량 총량)
#        n_r >= 1, 정수                       (권역당 최소 1대)
#
# shortage를 연속 보조변수로 두면 max(0, .)가 선형화되어 표준 MILP가 된다.
# ---------------------------------------------------------------------------

COST_UNDER_PER_PARCEL = 1500.0   # Cu: 미처리 1건당 페널티 (가정)
COST_OVER_PER_SLOT = 500.0       # Co: 유휴 용량 1건분 비용 (가정)
SCENARIO_WEIGHTS = {"q10": 0.3, "q50": 0.4, "q90": 0.3}  # Pearson-Tukey 3점 근사


def critical_ratio() -> float:
    return COST_UNDER_PER_PARCEL / (COST_UNDER_PER_PARCEL + COST_OVER_PER_SLOT)


def run_capacity_planning(
    forecast_predictions_path: Path,
    output_dir: Path,
    vehicle_daily_capacity: int | None = None,
    fleet_ratio: float = 0.92,
) -> pd.DataFrame:
    """quantile 예측 -> newsvendor 무제약해 -> 총량 제약 MILP 순으로 푼다.

    fleet_ratio < 1로 두어 총량 제약이 실제로 묶이게 하고(무제약해 대비 92%),
    제약이 어느 권역의 여유 용량부터 깎는지 비교표로 보인다.
    """
    import pulp

    output_dir.mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(forecast_predictions_path)
    needed = {"q10", "q50", "q75", "q90"}
    if not needed.issubset(pred.columns):
        raise ValueError(f"forecast_predictions.csv에 quantile 컬럼이 없습니다: {needed - set(pred.columns)}")

    # 권역 x 일자 총수요(카테고리 합) -> 권역별 일평균 수요 시나리오
    day_region = pred.groupby(["dest_region_id", "region_name", "date_key"], as_index=False)[
        ["prediction", "q10", "q50", "q75", "q90"]
    ].sum()
    region = day_region.groupby(["dest_region_id", "region_name"], as_index=False)[
        ["prediction", "q10", "q50", "q75", "q90"]
    ].mean()

    if vehicle_daily_capacity is None:
        # 평균 권역 수요의 1/5 수준으로 잡아 권역당 4~8대가 나오는 스케일 (설정값)
        vehicle_daily_capacity = int(round(region["q50"].mean() / 5 / 10) * 10) or 10

    q_star = critical_ratio()

    # ---- 1단계: 권역별 독립 newsvendor (무제약) ----
    # 용량 = q* 분위수 수요, 차량 = ceil(용량 / 대당 처리량)
    region["newsvendor_capacity"] = region["q75"]  # q* = 0.75
    region["vehicles_unconstrained"] = region["newsvendor_capacity"].apply(
        lambda c: max(1, math.ceil(c / vehicle_daily_capacity))
    )
    total_uncon = int(region["vehicles_unconstrained"].sum())
    fleet_limit = int(math.floor(total_uncon * fleet_ratio))

    # ---- 2단계: 총량 제약 MILP ----
    regions = region["dest_region_id"].tolist()
    demand = {
        (r, k): float(region.loc[region["dest_region_id"] == r, k].iloc[0])
        for r in regions for k in SCENARIO_WEIGHTS
    }

    prob = pulp.LpProblem("fleet_allocation", pulp.LpMinimize)
    n = pulp.LpVariable.dicts("vehicles", regions, lowBound=1, cat="Integer")
    s = pulp.LpVariable.dicts(
        "shortage", [(r, k) for r in regions for k in SCENARIO_WEIGHTS], lowBound=0, cat="Continuous"
    )

    prob += pulp.lpSum(
        COST_OVER_PER_SLOT * vehicle_daily_capacity * n[r]
        + pulp.lpSum(SCENARIO_WEIGHTS[k] * COST_UNDER_PER_PARCEL * s[(r, k)] for k in SCENARIO_WEIGHTS)
        for r in regions
    )
    for r in regions:
        for k in SCENARIO_WEIGHTS:
            prob += s[(r, k)] >= demand[(r, k)] - vehicle_daily_capacity * n[r]
    prob += pulp.lpSum(n[r] for r in regions) <= fleet_limit

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"MILP not optimal: {pulp.LpStatus[status]}")

    region["vehicles_milp"] = [int(round(n[r].value())) for r in regions]
    region["capacity_milp"] = region["vehicles_milp"] * vehicle_daily_capacity
    region["expected_shortage_q90"] = (region["q90"] - region["capacity_milp"]).clip(lower=0).round(1)
    region["cut_by_constraint"] = region["vehicles_unconstrained"] - region["vehicles_milp"]

    out_cols = [
        "dest_region_id", "region_name", "q10", "q50", "q75", "q90",
        "newsvendor_capacity", "vehicles_unconstrained", "vehicles_milp",
        "capacity_milp", "expected_shortage_q90", "cut_by_constraint",
    ]
    plan = region[out_cols].sort_values("q50", ascending=False).reset_index(drop=True)
    plan.round(1).to_csv(output_dir / "capacity_plan.csv", index=False, encoding="utf-8-sig")

    total_milp = int(plan["vehicles_milp"].sum())
    cut_regions = plan[plan["cut_by_constraint"] > 0]["region_name"].tolist()
    summary = f"""
# 권역별 차량 배분 (newsvendor + MILP)

## 비용 구조와 서비스 수준
- Cu(미처리 1건) = {COST_UNDER_PER_PARCEL:,.0f}원, Co(유휴 1건분) = {COST_OVER_PER_SLOT:,.0f}원 (가정치)
- Critical ratio q* = Cu/(Cu+Co) = **{q_star:.2f}** -> 수요 {q_star:.0%} 분위수만큼 용량 준비
- 차량 1대 일 처리량: **{vehicle_daily_capacity}건** (설정값)

## 결과
- 무제약 newsvendor 필요 차량: **{total_uncon}대**
- 총량 제약(F = {fleet_limit}대) MILP 배분: **{total_milp}대**
- 제약으로 감축된 권역: {', '.join(cut_regions) if cut_regions else '없음'}

## 해석
총량이 부족하면 MILP는 시나리오 기대 부족비용이 가장 덜 늘어나는 권역부터 깎는다.
수요 분산이 작은 권역은 q75와 q50 차이가 작아 한 대를 빼도 기대 페널티 증가가 작고,
그런 권역이 먼저 감축 대상이 된다. 권역별 독립 반올림으로는 이 우선순위가 안 나온다.

비용 상수와 대당 처리량은 도메인 가정이므로, 실제 적용 시 지연 배상 단가와
차량 운영비로 재추정해야 한다.
""".lstrip()
    (output_dir / "capacity_summary.md").write_text(summary, encoding="utf-8")
    return plan
