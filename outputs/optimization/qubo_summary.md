# QUBO 기반 거점 선택 실험

- 문제: 후보 허브 중 **2개** 선택
- 목적: 수요 커버리지 benefit 최대화 + 선택 개수 제약 penalty
- Penalty: **154.763** = 2 x max|benefit| + 1 (제약 위반 이득의 상계에서 유도)
- Best bitstring: `10100`
- 선택 허브: **서북권 MFC 후보, 동남권 MFC 후보**
- Energy: **-758.962**

## 검증
- 에너지 상위 10개 해가 전부 개수 제약(=2) 만족: **True**
- QUBO 최적해 = 제약 만족 해 중 benefit 최대 해: **True**

이 QUBO 행렬은 QAOA 또는 quantum annealing solver에 입력할 수 있는 quantum-ready formulation입니다. 현재 PoC는 외부 양자 SDK 없이 재현 가능하도록 brute force로 작은 문제를 검증합니다.
