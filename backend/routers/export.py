"""
Data Mining Export & Analytical Hub Router for Sreang Florist.
Provides CSV downloads for Google Colab (kmeans_rfm.csv & fp_growth.csv)
and live algorithm evaluation metrics for the Admin Dashboard.
"""

import csv
import io
import sqlite3
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from backend.database import get_db
from backend.analytics.rfm_kmeans import segment_customers_and_update
from backend.analytics.fp_growth import run_fpgrowth

router = APIRouter(prefix="/api", tags=["Analytics & Export"])


@router.get("/export/kmeans")
def export_kmeans_csv(db: sqlite3.Connection = Depends(get_db)):
    """
    Exports clean RFM dataset for Google Colab K-Means analysis.
    Output columns: Customer_ID, Nama_Pelanggan, Recency_Days, Frequency_Count, Monetary_Value
    """
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT 
            u.phone_number AS Customer_ID,
            u.name AS Nama_Pelanggan,
            CAST(julianday('now', 'localtime') - julianday(MAX(o.pickup_date)) AS INTEGER) AS Recency_Days,
            COUNT(o.id) AS Frequency_Count,
            SUM(o.total_price) AS Monetary_Value
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.role = 'customer' 
          AND o.status = 'Selesai'
        GROUP BY u.id, u.phone_number, u.name
        ORDER BY Monetary_Value DESC;
        """
    )
    rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Customer_ID", "Nama_Pelanggan", "Recency_Days", "Frequency_Count", "Monetary_Value"])

    for row in rows:
        writer.writerow([
            row["Customer_ID"],
            row["Nama_Pelanggan"],
            row["Recency_Days"],
            row["Frequency_Count"],
            row["Monetary_Value"],
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=kmeans_rfm.csv"},
    )


@router.get("/export/fpgrowth")
def export_fpgrowth_csv(db: sqlite3.Connection = Depends(get_db)):
    """
    Exports transactional itemsets dataset for Google Colab FP-Growth analysis.
    Output columns: Transaction_ID, Itemsets
    """
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT 
            o.id AS Transaction_ID,
            GROUP_CONCAT(ma.name, ', ') AS Itemsets
        FROM orders o
        JOIN order_customizations oc ON o.id = oc.order_id
        JOIN master_attributes ma ON oc.attribute_id = ma.id
        WHERE o.status = 'Selesai'
        GROUP BY o.id
        ORDER BY o.id ASC;
        """
    )
    rows = cursor.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Transaction_ID", "Itemsets"])

    for row in rows:
        writer.writerow([row["Transaction_ID"], row["Itemsets"]])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fp_growth.csv"},
    )


@router.get("/analytics/summary")
def get_analytics_summary(db: sqlite3.Connection = Depends(get_db)):
    """
    Returns live analytical metrics for the Admin Dashboard:
    - Silhouette Score, cluster sizes, and RFM centroid profiles.
    - FP-Growth frequent patterns, support, confidence, and lift ratios.
    """
    # 1. K-Means Status
    kmeans_result = segment_customers_and_update(db)

    # 2. FP-Growth Status
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT o.id, ma.name
        FROM orders o
        JOIN order_customizations oc ON o.id = oc.order_id
        JOIN master_attributes ma ON oc.attribute_id = ma.id
        WHERE o.status = 'Selesai'
        ORDER BY o.id
        """
    )
    rows = cursor.fetchall()

    transactions_dict = {}
    for r in rows:
        order_id = r["id"]
        if order_id not in transactions_dict:
            transactions_dict[order_id] = []
        transactions_dict[order_id].append(r["name"])

    transactions = list(transactions_dict.values())
    fpgrowth_result = run_fpgrowth(transactions, min_support=0.15, min_confidence=0.50)

    return {
        "kmeans": {
            "silhouette_score": kmeans_result["silhouette_score"],
            "clusters": kmeans_result["clusters"],
            "total_segmented_customers": kmeans_result["total_segmented_customers"],
            "customers": kmeans_result["customers"][:10],
        },
        "fp_growth": {
            "total_mined_transactions": fpgrowth_result["total_transactions"],
            "total_rules": len(fpgrowth_result["rules"]),
            "top_rules": fpgrowth_result["rules"][:8],
            "frequent_itemsets": fpgrowth_result["frequent_itemsets"][:8],
        },
    }


@router.post("/analytics/recalculate")
def recalculate_analytics(db: sqlite3.Connection = Depends(get_db)):
    """
    Force updates customer tiers using latest RFM K-Means calculation.
    """
    result = segment_customers_and_update(db)
    return {
        "success": True,
        "message": "Model K-Means RFM berhasil dikalkulasi ulang.",
        "silhouette_score": result["silhouette_score"],
        "clusters": result["clusters"],
    }
