from pathlib import Path
import pandas as pd

def test_qubo_bitstring_and_feasibility():
    s = Path('outputs/advanced_analytics/qubo/qubo_solution_extended.csv')
    m = Path('outputs/advanced_analytics/qubo/qubo_matrix_extended.csv')
    if not (s.exists() and m.exists()):
        return
    sol = pd.read_csv(s, dtype={'bitstring': str})
    mat = pd.read_csv(m)
    n = len(mat)
    assert (sol['bitstring'].str.len() == n).all()
    assert sol['is_feasible_select_k'].astype(bool).any()
