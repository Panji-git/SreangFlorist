"""
Python Native K-Means & RFM Segmentation Module.
Computes Recency, Frequency, and Monetary (RFM) metrics from SQLite,
normalizes features, clusters customers into loyalty tiers (Gold, Silver, Bronze),
calculates the academic Silhouette Score, and updates tier_status in the database.
Pure Python implementation (no scipy/scikit-learn dependency required).
"""

from collections import defaultdict
import math
import random
import sqlite3
from typing import Dict, List, Tuple, Any, Optional


def extract_rfm_data(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Extracts Recency, Frequency, and Monetary values for customers with completed orders.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            u.id AS user_id,
            u.phone_number AS customer_id,
            u.name AS customer_name,
            u.tier_status AS current_tier,
            u.total_points AS points,
            CAST(julianday('now', 'localtime') - julianday(MAX(o.pickup_date)) AS INTEGER) AS recency,
            COUNT(o.id) AS frequency,
            SUM(o.total_price) AS monetary
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.role = 'customer' 
          AND o.status = 'Selesai'
        GROUP BY u.id, u.phone_number, u.name
        ORDER BY monetary DESC
        """
    )
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


def min_max_normalize(data: List[List[float]]) -> Tuple[List[List[float]], List[Tuple[float, float]]]:
    """
    Normalizes each column to [0, 1] range.
    Returns (normalized_data, column_min_max_bounds).
    """
    if not data:
        return [], []

    num_rows = len(data)
    num_cols = len(data[0])
    bounds = []
    normalized = [[0.0] * num_cols for _ in range(num_rows)]

    for c in range(num_cols):
        col_vals = [data[r][c] for r in range(num_rows)]
        min_v = min(col_vals)
        max_v = max(col_vals)
        range_v = max_v - min_v if max_v > min_v else 1.0
        bounds.append((min_v, max_v))

        for r in range(num_rows):
            normalized[r][c] = (data[r][c] - min_v) / range_v

    return normalized, bounds


def euclidean_distance(p1: List[float], p2: List[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))


def run_kmeans(
    data: List[List[float]],
    k: int = 3,
    max_iter: int = 100,
    random_seed: int = 42,
) -> Tuple[List[int], List[List[float]]]:
    """
    Pure Python K-Means clustering.
    Returns (cluster_labels, final_centroids).
    """
    n = len(data)
    if n == 0:
        return [], []
    if n <= k:
        return list(range(n)), data

    rng = random.Random(random_seed)

    # 1. K-Means++ style initialization
    centroids = [data[rng.randint(0, n - 1)]]
    for _ in range(1, k):
        distances = []
        for point in data:
            min_d = min(euclidean_distance(point, c) for c in centroids)
            distances.append(min_d ** 2)
        total_d = sum(distances)
        if total_d == 0:
            centroids.append(data[rng.randint(0, n - 1)])
            continue
        probs = [d / total_d for d in distances]
        # Choose next centroid with roulette wheel
        r = rng.random()
        cum = 0.0
        chosen_idx = 0
        for i, p in enumerate(probs):
            cum += p
            if cum >= r:
                chosen_idx = i
                break
        centroids.append(data[chosen_idx])

    labels = [0] * n

    # 2. Iterations
    for _ in range(max_iter):
        # Assignment step
        changed = False
        for i in range(n):
            closest_c = 0
            closest_dist = float("inf")
            for c_idx, c in enumerate(centroids):
                d = euclidean_distance(data[i], c)
                if d < closest_dist:
                    closest_dist = d
                    closest_c = c_idx
            if labels[i] != closest_c:
                labels[i] = closest_c
                changed = True

        if not changed:
            break

        # Update step
        dim = len(data[0])
        new_centroids = []
        for c_idx in range(k):
            members = [data[i] for i in range(n) if labels[i] == c_idx]
            if members:
                mean_point = [
                    sum(m[d] for m in members) / len(members) for d in range(dim)
                ]
                new_centroids.append(mean_point)
            else:
                # Re-seed empty cluster to random point
                new_centroids.append(data[rng.randint(0, n - 1)])
        centroids = new_centroids

    return labels, centroids


def calculate_silhouette_score(data: List[List[float]], labels: List[int], k: int) -> float:
    """
    Calculates the mean Silhouette Score for academic validation.
    Score ranges from -1.0 to +1.0 (higher is better clustering).
    """
    n = len(data)
    if n <= k or k < 2:
        return 0.0

    cluster_members = defaultdict(list)
    for i, label in enumerate(labels):
        cluster_members[label].append(i)

    silhouette_values = []
    for i in range(n):
        own_cluster = labels[i]
        own_members = cluster_members[own_cluster]

        if len(own_members) <= 1:
            silhouette_values.append(0.0)
            continue

        # a(i): average distance to own cluster members
        a_i = sum(euclidean_distance(data[i], data[j]) for j in own_members if j != i) / (len(own_members) - 1)

        # b(i): minimum average distance to other clusters
        min_b_i = float("inf")
        for other_cluster, members in cluster_members.items():
            if other_cluster == own_cluster or not members:
                continue
            mean_dist = sum(euclidean_distance(data[i], data[j]) for j in members) / len(members)
            if mean_dist < min_b_i:
                min_b_i = mean_dist

        b_i = min_b_i if min_b_i != float("inf") else 0.0
        max_ab = max(a_i, b_i)
        s_i = (b_i - a_i) / max_ab if max_ab > 0 else 0.0
        silhouette_values.append(s_i)

    return round(sum(silhouette_values) / len(silhouette_values), 4)


def segment_customers_and_update(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Executes RFM segmentation, updates customer tier_status, and returns analytical summary.
    """
    rfm_records = extract_rfm_data(conn)
    if not rfm_records:
        return {
            "success": False,
            "message": "Belum ada transaksi 'Selesai' untuk segmentasi.",
            "silhouette_score": 0.0,
            "clusters": [],
            "customers": [],
        }

    # Features: [Recency, Frequency, Monetary]
    # For RFM: lower Recency is better, higher Frequency is better, higher Monetary is better.
    # We invert recency for score ranking (so higher is always better)
    max_rec = max(r["recency"] for r in rfm_records) or 1
    raw_features = [
        [float(r["recency"]), float(r["frequency"]), float(r["monetary"])]
        for r in rfm_records
    ]

    normalized_features, bounds = min_max_normalize(raw_features)
    k = min(3, len(rfm_records))
    labels, centroids = run_kmeans(normalized_features, k=k)
    silhouette = calculate_silhouette_score(normalized_features, labels, k=k)

    # Calculate composite score for each cluster centroid to assign tier labels
    # Composite RFM: (1 - norm_recency)*0.2 + norm_freq*0.4 + norm_monetary*0.4
    cluster_scores = []
    for c_idx in range(k):
        members_idx = [i for i, lbl in enumerate(labels) if lbl == c_idx]
        if members_idx:
            avg_rec = sum(raw_features[i][0] for i in members_idx) / len(members_idx)
            avg_freq = sum(raw_features[i][1] for i in members_idx) / len(members_idx)
            avg_mon = sum(raw_features[i][2] for i in members_idx) / len(members_idx)
            # Rank score: high frequency & high monetary & low recency = highest score
            score = (avg_freq * 0.4) + ((avg_mon / 100000.0) * 0.5) - (avg_rec * 0.1)
            cluster_scores.append((c_idx, score, avg_rec, avg_freq, avg_mon, len(members_idx)))
        else:
            cluster_scores.append((c_idx, -999, 0, 0, 0, 0))

    # Sort descending by score
    cluster_scores.sort(key=lambda x: x[1], reverse=True)
    tier_names = ["Gold Tier", "Silver Tier", "Bronze Tier"]

    cluster_to_tier = {}
    cluster_summaries = []
    for rank, (c_idx, score, avg_rec, avg_freq, avg_mon, size) in enumerate(cluster_scores):
        tier_label = tier_names[rank] if rank < len(tier_names) else f"Cluster {rank+1}"
        cluster_to_tier[c_idx] = tier_label
        cluster_summaries.append({
            "cluster_index": c_idx,
            "tier_label": tier_label,
            "size": size,
            "avg_recency_days": round(avg_rec, 1),
            "avg_frequency": round(avg_freq, 1),
            "avg_monetary_rp": round(avg_mon, 2),
            "composite_score": round(score, 2),
        })

    # Update database customer tier_status
    cursor = conn.cursor()
    enriched_customers = []
    for i, r in enumerate(rfm_records):
        c_idx = labels[i]
        new_tier = cluster_to_tier[c_idx]
        cursor.execute(
            "UPDATE users SET tier_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_tier, r["user_id"]),
        )
        r_copy = dict(r)
        r_copy["cluster_index"] = c_idx
        r_copy["assigned_tier"] = new_tier
        enriched_customers.append(r_copy)

    conn.commit()

    return {
        "success": True,
        "k": k,
        "silhouette_score": silhouette,
        "clusters": cluster_summaries,
        "total_segmented_customers": len(rfm_records),
        "customers": enriched_customers,
    }
