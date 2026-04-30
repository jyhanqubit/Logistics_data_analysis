from pathlib import Path
import pandas as pd

def test_clustering_geo_range():
    p = Path('outputs/advanced_analytics/clustering/cluster_assignments.csv')
    if not p.exists():
        return
    df = pd.read_csv(p)
    assert not df['region_name'].astype(str).str.startswith('Region-').any()
    assert df['lat'].between(37.3, 37.8).all()
    assert df['lon'].between(126.7, 127.3).all()
