# Optimization Formulation

## CVRP
Objective: $\min \sum_{k\in K}\sum_i\sum_{j\neq i} d_{ij}x_{ijk}$
- 의미: 차량 k가 노드 i→j로 이동하면($x_{ijk}=1$) 해당 거리 $d_{ij}$가 비용으로 더해집니다.
- 해석: 선택된 이동 간선들의 총 거리를 최소화하는 경로를 찾습니다.

## Facility Location
Objective: $\max \sum_i\sum_j demand_i y_{ij} - \lambda\sum_j cost_j z_j$
- 의미: 수요 커버리지 이익(첫 항)에서 거점 설치/운영 비용(둘째 항)을 뺀 순가치를 최대화합니다.
- 해석: 수요가 큰 지역을 커버하면서도 비용이 과도한 거점은 피합니다.

## QUBO
Objective: $\min x^TQx$ with benefit, select-k, overlap, cost penalties.
- 의미: 거점 선택 여부를 0/1 벡터 $x$로 두고, 목적/제약을 행렬 $Q$의 에너지 최소화 문제로 변환합니다.
- 해석: 에너지가 낮을수록 (i) 커버 이익이 높고 (ii) 선택 개수/중복/비용 페널티를 덜 위반하는 조합입니다.
