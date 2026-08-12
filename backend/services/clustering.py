"""
============================================================
Clustering Service — Unsupervised K-Means Clustering
============================================================
ML Concept: Unsupervised Learning — K-Means Clustering
Library:    scikit-learn

Uses the Elbow Method to automatically find the optimal
number of clusters K (range 2–8) by minimising inertia.

Falls back gracefully if scikit-learn is not installed.
============================================================
"""

from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# ── Try scikit-learn ──────────────────────────────────────
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("Clustering: scikit-learn not installed — clustering disabled")


# ─────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────

def cluster_dataframe(
    df: pd.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    max_k: int = 8,
    label_col: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run K-Means clustering on numeric columns of the DataFrame.

    Parameters:
        df:           Input DataFrame
        numeric_cols: Columns to cluster on (None = all numeric)
        max_k:        Maximum clusters to evaluate with elbow method
        label_col:    Optional categorical column to describe clusters

    Returns:
        {
            "optimal_k": int,
            "cluster_sizes": dict {cluster_id: count},
            "cluster_centers": list of dicts,
            "data_with_clusters": list of dicts (first 200 rows),
            "inertia_values": list (elbow curve data),
            "method": str,
        }
    """
    if not _SKLEARN_AVAILABLE:
        return {
            "optimal_k": 0,
            "cluster_sizes": {},
            "cluster_centers": [],
            "data_with_clusters": [],
            "inertia_values": [],
            "method": "unavailable",
            "message": "scikit-learn not installed. Run: pip install scikit-learn",
        }

    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    if len(numeric_cols) < 1:
        return {
            "optimal_k": 0,
            "cluster_sizes": {},
            "cluster_centers": [],
            "data_with_clusters": [],
            "inertia_values": [],
            "method": "none",
            "message": "No numeric columns available for clustering.",
        }

    # ── Prepare data ──────────────────────────────────────
    df_num = df[numeric_cols].dropna()
    if len(df_num) < 4:
        return {
            "optimal_k": 0,
            "cluster_sizes": {},
            "cluster_centers": [],
            "data_with_clusters": [],
            "inertia_values": [],
            "method": "none",
            "message": "Not enough data rows for clustering (need ≥ 4).",
        }

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_num)

    # ── PCA dimensionality reduction (when features > 5) ──
    # Reduces correlated features and noise, improving cluster
    # separation quality on wide datasets significantly.
    pca_used = False
    explained_variance = None
    n_features = X_scaled.shape[1]

    if n_features > 5:
        # Retain enough components to explain 95% of variance
        pca = PCA(n_components=0.95, random_state=42)
        X_for_clustering = pca.fit_transform(X_scaled)
        pca_used = True
        n_components = X_for_clustering.shape[1]
        explained_variance = round(float(pca.explained_variance_ratio_.sum()) * 100, 1)
        logger.info(
            "Clustering: PCA: %d features → %d components (%.1f%% variance retained)",
            n_features, n_components, explained_variance,
        )
    else:
        X_for_clustering = X_scaled

    # ── Elbow Method to find optimal K ───────────────────
    k_range = range(2, min(max_k + 1, len(df_num) // 2 + 1, 9))
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_for_clustering)
        inertias.append(float(km.inertia_))

    optimal_k = _find_elbow(list(k_range), inertias)

    # ── Final clustering with optimal K ──────────────────
    final_km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    cluster_labels = final_km.fit_predict(X_for_clustering)

    # ── Add cluster column to DataFrame ──────────────────
    df_result = df.loc[df_num.index].copy()
    df_result["cluster"] = cluster_labels

    # Cluster sizes
    cluster_sizes = df_result["cluster"].value_counts().to_dict()
    cluster_sizes = {int(k): int(v) for k, v in cluster_sizes.items()}

    # Cluster centers — always inverse-transform back to original scale
    # for interpretability regardless of whether PCA was used
    centers_pca = final_km.cluster_centers_
    if pca_used:
        centers_scaled = pca.inverse_transform(centers_pca)
    else:
        centers_scaled = centers_pca
    centers_original = scaler.inverse_transform(centers_scaled)
    cluster_centers = [
        {col: round(float(val), 4) for col, val in zip(numeric_cols, center)}
        for center in centers_original
    ]

    # Describe each cluster with label column if provided
    cluster_descriptions = {}
    if label_col and label_col in df_result.columns:
        for cid in range(optimal_k):
            top_labels = (
                df_result[df_result["cluster"] == cid][label_col]
                .value_counts()
                .head(3)
                .index.tolist()
            )
            cluster_descriptions[int(cid)] = top_labels

    return {
        "optimal_k":         int(optimal_k),
        "cluster_sizes":     cluster_sizes,
        "cluster_centers":   cluster_centers,
        "cluster_descriptions": cluster_descriptions,
        "data_with_clusters": df_result.head(200).to_dict(orient="records"),
        "inertia_values": [
            {"k": int(k), "inertia": round(v, 2)}
            for k, v in zip(k_range, inertias)
        ],
        "columns_used":      numeric_cols,
        "method":            "kmeans+pca" if pca_used else "kmeans",
        "pca_used":          pca_used,
        "pca_variance_retained_pct": explained_variance,
        "rows_clustered":    int(len(df_num)),
    }


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def _find_elbow(k_values: List[int], inertias: List[float]) -> int:
    """
    Find the elbow point in the inertia curve.
    Uses the maximum distance from the straight line
    connecting the first and last points (knee detection).
    """
    if not k_values:
        return 2  # Minimum fallback — need at least 2 clusters
    if len(k_values) <= 1:
        return k_values[0]

    # Normalise points to [0, 1]
    x = np.array(k_values, dtype=float)
    y = np.array(inertias, dtype=float)

    x_norm = (x - x.min()) / (x.max() - x.min() + 1e-9)
    y_norm = (y - y.min()) / (y.max() - y.min() + 1e-9)

    # Line from first to last point
    line_vec = np.array([x_norm[-1] - x_norm[0], y_norm[-1] - y_norm[0]])
    line_len = np.linalg.norm(line_vec)

    # Distance of each point from the line
    distances = []
    for xi, yi in zip(x_norm, y_norm):
        point_vec = np.array([xi - x_norm[0], yi - y_norm[0]])
        cross = abs(line_vec[0] * point_vec[1] - line_vec[1] * point_vec[0])
        distances.append(cross / (line_len + 1e-9))

    elbow_idx = int(np.argmax(distances))
    return k_values[elbow_idx]
