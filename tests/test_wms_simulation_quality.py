from pathlib import Path
import pandas as pd

def test_wms_distribution_quality():
    p = Path('outputs/analysis_cases/03_wms_inventory_risk.csv')
    if not p.exists():
        return
    df = pd.read_csv(p)
    assert df['warehouse_id'].nunique() >= 3
    assert df['product_category'].nunique() >= 5
    assert (df['stockout_risk_score'].fillna(0) > 0).any()
