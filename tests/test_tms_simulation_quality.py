from pathlib import Path
import pandas as pd

def test_tms_distribution_quality():
    p = Path('outputs/analysis_cases/05_tms_delivery_sla.csv')
    if not p.exists():
        return
    df = pd.read_csv(p)
    assert df['region_name'].nunique() >= 10
    assert df['on_time_delivery_rate'].nunique() > 2
    assert df['late_delivery_risk_score'].nunique() > 10
