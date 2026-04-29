from __future__ import annotations

import numpy as np

from parcelflow.advanced_analytics.clustering import dunn_index


def test_dunn_index_positive_or_nan() -> None:
    X = np.array([[0, 0], [0, 1], [5, 5], [5, 6]], dtype=float)
    labels = np.array([0, 0, 1, 1])
    d = dunn_index(X, labels)
    assert (d > 0) or np.isnan(d)
