from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .data_generator import haversine_km
from .db import query_df


def _route_distance(route: list[int], coords: dict[int, tuple[float, float]], depot_id: int) -> float:
    if not route:
        return 0.0
    full = [depot_id] + route + [depot_id]
    dist = 0.0
    for a, b in zip(full, full[1:]):
        dist += haversine_km(coords[a][0], coords[a][1], coords[b][0], coords[b][1])
    return dist


def _nearest_neighbor(nodes: list[int], coords: dict[int, tuple[float, float]], depot_id: int) -> list[int]:
    remaining = set(nodes)
    route: list[int] = []
    current = depot_id
    while remaining:
        nxt = min(remaining, key=lambda n: haversine_km(coords[current][0], coords[current][1], coords[n][0], coords[n][1]))
        route.append(nxt)
        remaining.remove(nxt)
        current = nxt
    return route


def _two_opt(route: list[int], coords: dict[int, tuple[float, float]], depot_id: int, max_iter: int = 50) -> list[int]:
    best = route[:]
    best_dist = _route_distance(best, coords, depot_id)
    improved = True
    n_iter = 0
    while improved and n_iter < max_iter:
        improved = False
        n_iter += 1
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i:j][::-1] + best[j:]
                cand_dist = _route_distance(candidate, coords, depot_id)
                if cand_dist + 1e-9 < best_dist:
                    best = candidate
                    best_dist = cand_dist
                    improved = True
    return best


def solve_cvrp_greedy(db_path: Path, recommendations_path: Path, output_dir: Path, max_nodes: int = 12, vehicle_capacity: int = 2800) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    rec = pd.read_csv(recommendations_path)
    top_regions = rec[rec["recommendation_type"] == "Parcel Locker"].sort_values("rank").head(max_nodes)["region_name"].tolist()

    nodes = query_df(db_path, """
        SELECT r.region_id, r.region_name, r.lat, r.lon, SUM(f.inbound_volume) AS total_volume
        FROM dim_region r
        JOIN fact_daily_demand f ON r.region_id = f.dest_region_id
        GROUP BY r.region_id, r.region_name, r.lat, r.lon
    """)
    nodes = nodes[nodes["region_name"].isin(top_regions)].copy()
    if nodes.empty:
        raise ValueError("No nodes selected for route optimization.")

    # 중부권 후보를 depot으로 사용
    depot = query_df(db_path, "SELECT hub_id, hub_name, lat, lon FROM dim_hub_candidate WHERE hub_name LIKE '%중부권%' LIMIT 1").iloc[0]
    depot_id = 0
    coords = {depot_id: (float(depot["lat"]), float(depot["lon"]))}
    demand = {}
    for _, row in nodes.iterrows():
        node_id = int(row["region_id"])
        coords[node_id] = (float(row["lat"]), float(row["lon"]))
        # 일평균 물동량 중 일부를 라스트마일 배송 물량으로 간주
        demand[node_id] = max(80, int(row["total_volume"] / 210 / 3))

    # 용량 기준으로 차량 route 분할: 수요 큰 순서로 bin packing 후 각 route를 2-opt
    sorted_nodes = sorted(demand.keys(), key=lambda n: demand[n], reverse=True)
    routes: list[list[int]] = []
    route_loads: list[int] = []
    for node in sorted_nodes:
        placed = False
        for idx, load in enumerate(route_loads):
            if load + demand[node] <= vehicle_capacity:
                routes[idx].append(node)
                route_loads[idx] += demand[node]
                placed = True
                break
        if not placed:
            routes.append([node])
            route_loads.append(demand[node])

    rows = []
    for vehicle_id, route_nodes in enumerate(routes, start=1):
        nn = _nearest_neighbor(route_nodes, coords, depot_id)
        opt = _two_opt(nn, coords, depot_id)
        dist = _route_distance(opt, coords, depot_id)
        load = sum(demand[n] for n in opt)
        for seq, node_id in enumerate(opt, start=1):
            node_row = nodes[nodes["region_id"] == node_id].iloc[0]
            rows.append({
                "vehicle_id": vehicle_id,
                "stop_sequence": seq,
                "region_id": node_id,
                "region_name": node_row["region_name"],
                "node_demand": demand[node_id],
                "vehicle_load": load,
                "vehicle_capacity": vehicle_capacity,
                "route_distance_km": round(dist, 2),
            })
    route_plan = pd.DataFrame(rows)
    route_plan.to_csv(output_dir / "route_plan.csv", index=False, encoding="utf-8-sig")

    total_distance = route_plan.groupby("vehicle_id")["route_distance_km"].first().sum()
    summary = f"""
# 배송 경로 최적화 요약

- 알고리즘: capacity-aware greedy bin packing + nearest neighbor + 2-opt 개선
- 차량 수: **{route_plan['vehicle_id'].nunique()}대**
- 총 이동거리: **{total_distance:.2f} km**
- 차량 용량: **{vehicle_capacity:,} units**

실제 포트폴리오 확장 시 OR-Tools CVRP solver를 붙이면 동일한 입력 데이터로 최적해/휴리스틱해 비교가 가능합니다.
""".lstrip()
    (output_dir / "route_summary.md").write_text(summary, encoding="utf-8")
    return route_plan


def build_facility_qubo(db_path: Path, k: int = 2, penalty: float = 1000.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a small QUBO for selecting k hubs from candidates.

    Objective sketch:
        minimize -benefit_i * x_i + penalty * (sum_i x_i - k)^2

    benefit_i approximates demand coverage around each candidate hub.
    This is quantum-ready: QUBO matrix can be sent to QAOA/annealing solvers.
    """
    hubs = query_df(db_path, "SELECT hub_id, hub_name, lat, lon, capacity_daily, fixed_cost_score FROM dim_hub_candidate")
    demand = query_df(db_path, """
        SELECT r.region_id, r.region_name, r.lat, r.lon, SUM(f.inbound_volume) AS total_volume
        FROM dim_region r
        JOIN fact_daily_demand f ON r.region_id = f.dest_region_id
        GROUP BY r.region_id, r.region_name, r.lat, r.lon
    """)
    benefits = []
    for _, h in hubs.iterrows():
        coverage = 0.0
        for _, d in demand.iterrows():
            dist = haversine_km(float(h["lat"]), float(h["lon"]), float(d["lat"]), float(d["lon"]))
            coverage += float(d["total_volume"]) / (1.0 + dist)
        benefit = coverage / 10000.0 - float(h["fixed_cost_score"]) * 30
        benefits.append(benefit)
    hubs = hubs.copy()
    hubs["benefit"] = benefits

    n = len(hubs)
    q = np.zeros((n, n), dtype=float)
    # penalty * (sum x - k)^2 = penalty*(sum x_i + 2 sum_i<j x_i x_j - 2k sum x_i + k^2)
    for i in range(n):
        q[i, i] += -float(hubs.loc[i, "benefit"]) + penalty * (1 - 2 * k)
        for j in range(i + 1, n):
            q[i, j] += 2 * penalty
    qubo = pd.DataFrame(q, columns=[f"x_{int(h)}" for h in hubs["hub_id"]], index=[f"x_{int(h)}" for h in hubs["hub_id"]])
    return hubs, qubo


def solve_qubo_bruteforce(hubs: pd.DataFrame, qubo: pd.DataFrame) -> pd.DataFrame:
    q = qubo.to_numpy()
    n = q.shape[0]
    rows = []
    for bits in itertools.product([0, 1], repeat=n):
        x = np.array(bits)
        energy = float(x @ q @ x)
        selected = hubs.loc[[i for i, b in enumerate(bits) if b == 1], "hub_name"].tolist()
        rows.append({
            "bits": "".join(map(str, bits)),
            "selected_count": int(x.sum()),
            "energy": energy,
            "selected_hubs": ", ".join(selected),
        })
    return pd.DataFrame(rows).sort_values("energy").reset_index(drop=True)


def run_qubo_experiment(db_path: Path, output_dir: Path, k: int = 2) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    hubs, qubo = build_facility_qubo(db_path, k=k)
    solutions = solve_qubo_bruteforce(hubs, qubo)
    qubo.to_csv(output_dir / "qubo_matrix.csv", encoding="utf-8-sig")
    hubs.to_csv(output_dir / "qubo_hub_benefits.csv", index=False, encoding="utf-8-sig")
    solutions.to_csv(output_dir / "qubo_solution.csv", index=False, encoding="utf-8-sig")
    best = solutions.iloc[0]
    summary = f"""
# QUBO 기반 거점 선택 실험

- 문제: 후보 허브 중 **{k}개** 선택
- 목적: 수요 커버리지 benefit 최대화 + 선택 개수 제약 penalty
- Best bitstring: `{best['bits']}`
- 선택 허브: **{best['selected_hubs']}**
- Energy: **{float(best['energy']):.3f}**

이 QUBO 행렬은 QAOA 또는 quantum annealing solver에 입력할 수 있는 quantum-ready formulation입니다. 현재 PoC는 외부 양자 SDK 없이 재현 가능하도록 brute force로 작은 문제를 검증합니다.
""".lstrip()
    (output_dir / "qubo_summary.md").write_text(summary, encoding="utf-8")
    return solutions
