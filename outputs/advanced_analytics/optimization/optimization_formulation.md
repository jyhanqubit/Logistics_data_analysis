# Optimization Formulation

## CVRP
Objective: $\min \sum_{k\in K}\sum_i\sum_{j\neq i} d_{ij}x_{ijk}$

## Facility Location
Objective: $\max \sum_i\sum_j demand_i y_{ij} - \lambda\sum_j cost_j z_j$

## QUBO
Objective: $\min x^TQx$ with benefit, select-k, overlap, cost penalties.
