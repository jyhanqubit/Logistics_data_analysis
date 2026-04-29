# QUBO / Quantum-ready Explanation

- 현재 QUBO는 후보지 선택 문제를 binary variable로 모델링한 formulation입니다.
- 이 레포는 **실제 양자컴퓨터 실행 결과가 아니라**, classical brute force로 검증한 quantum-ready PoC입니다.
- QUBO matrix가 5x5이고 bitstring 길이가 5라면 5개 binary variable 문제입니다.
- QAOA 관점에서는 5-qubit 매핑 가능성을 설명할 수 있으나, 실제 5-qubit 하드웨어 실험 수행으로 표현하면 안 됩니다.
- 확장 방향: QAOA/quantum annealing 매핑 실험 + classical heuristic 비교.
