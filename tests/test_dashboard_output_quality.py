from pathlib import Path
import pandas as pd
from parcelflow.advanced_analytics.validation import assert_no_placeholder_text

def _read(p: str):
    path = Path(p)
    return pd.read_csv(path) if path.exists() else pd.DataFrame()

def test_no_placeholder_tokens_in_actions():
    df = _read('outputs/insights/business_action_recommendations.csv')
    if df.empty:
        return
    assert_no_placeholder_text(df[['recommended_action','business_finding']])
