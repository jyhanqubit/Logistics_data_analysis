from pathlib import Path
import pandas as pd

def test_action_quality_columns_and_rows():
    p = Path('outputs/insights/business_action_recommendations.csv')
    if not p.exists():
        return
    df = pd.read_csv(p)
    required = {'action_id','priority','area','business_finding','recommended_action','expected_impact_score','implementation_urgency','action_value'}
    assert required.issubset(df.columns)
    assert len(df) >= 8
    assert df['recommended_action'].notna().all()
