from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

SEOUL_CENTROIDS = {
    "강남구": (37.5172, 127.0473), "송파구": (37.5145, 127.1059), "강서구": (37.5509, 126.8495),
    "마포구": (37.5663, 126.9019), "관악구": (37.4784, 126.9516), "종로구": (37.5729, 126.9793),
}


def dunn_index(X: np.ndarray, labels: np.ndarray) -> float:
    uniq = np.unique(labels)
    if len(uniq) < 2:
        return np.nan
    intra = []
    inter = []
    for c in uniq:
        pts = X[labels == c]
        if len(pts) < 2:
            intra.append(0)
        else:
            d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(axis=2))
            intra.append(np.nanmax(d))
    max_intra = max(intra) if intra else np.nan
    for i, c1 in enumerate(uniq):
        for c2 in uniq[i + 1:]:
            p1, p2 = X[labels == c1], X[labels == c2]
            d = np.sqrt(((p1[:, None, :] - p2[None, :, :]) ** 2).sum(axis=2))
            inter.append(np.nanmin(d))
    min_inter = min(inter) if inter else np.nan
    if not max_intra or np.isnan(max_intra):
        return np.nan
    return float(min_inter / max_intra)


def run_clustering_analysis(feature_df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)

    grp = feature_df.groupby("dest_region_id", as_index=False).agg(
        avg_volume=("inbound_volume", "mean"),
        cv=("inbound_volume", lambda s: float(np.std(s) / max(1, np.mean(s)))),
        peak_ratio=("is_peak_season", "mean"),
        growth_rate=("demand_spike_score", "mean"),
        category_entropy=("category_entropy_by_region", "mean"),
    )
    grp["region_name"] = "Region-" + grp["dest_region_id"].astype(str)
    grp["locker_score"] = grp["avg_volume"] * (1 + grp["growth_rate"].fillna(0))

    X = grp[["avg_volume", "cv", "peak_ratio", "growth_rate", "category_entropy", "locker_score"]].fillna(0).to_numpy()
    Xs = StandardScaler().fit_transform(X)

    quality = []
    assign_frames = []
    for k in range(2, min(9, len(grp))):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(Xs)
        labels = km.labels_
        quality.append({
            "model": "KMeans", "k": k,
            "silhouette": silhouette_score(Xs, labels) if len(np.unique(labels)) > 1 else np.nan,
            "davies_bouldin": davies_bouldin_score(Xs, labels) if len(np.unique(labels)) > 1 else np.nan,
            "calinski_harabasz": calinski_harabasz_score(Xs, labels) if len(np.unique(labels)) > 1 else np.nan,
            "dunn_index": dunn_index(Xs, labels),
        })

    best_k = int(pd.DataFrame(quality).sort_values("silhouette", ascending=False).iloc[0]["k"]) if quality else 2
    model = KMeans(n_clusters=best_k, random_state=42, n_init=10).fit(Xs)
    labels = model.labels_

    out = grp.copy()
    out["cluster_id"] = labels
    out["cluster_label"] = out["cluster_id"].map(lambda x: f"Cluster-{x}")
    out["lat"] = out["region_name"].map(lambda x: SEOUL_CENTROIDS.get(x, (37.55, 126.98))[0])
    out["lon"] = out["region_name"].map(lambda x: SEOUL_CENTROIDS.get(x, (37.55, 126.98))[1])
    out["business_interpretation"] = "수요/변동성 특성이 유사한 지역군"
    out["recommended_action"] = "군집별 차등 재고/배차 운영"

    profiles = out.groupby("cluster_id", as_index=False)[["avg_volume", "cv", "peak_ratio", "growth_rate", "locker_score"]].mean()
    centroids = out[["region_name", "lat", "lon"]].copy()

    assignments_path = out_dir / "cluster_assignments.csv"
    profiles_path = out_dir / "cluster_profiles.csv"
    quality_path = out_dir / "cluster_quality_scores.csv"
    centroid_path = out_dir / "seoul_district_centroids.csv"
    summary_path = out_dir / "clustering_summary.md"

    out.to_csv(assignments_path, index=False, encoding="utf-8-sig")
    profiles.to_csv(profiles_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(quality).to_csv(quality_path, index=False, encoding="utf-8-sig")
    centroids.to_csv(centroid_path, index=False, encoding="utf-8-sig")
    summary_path.write_text("# Clustering Summary\n\n지역 군집 기반 차등 운영전략 수립에 활용합니다.\n", encoding="utf-8")

    return {"assignments": assignments_path, "profiles": profiles_path, "quality": quality_path, "centroids": centroid_path, "summary": summary_path}
