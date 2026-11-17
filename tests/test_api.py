"""
Integration tests for Sreang Florist REST API and Analytics.
"""

from fastapi.testclient import TestClient
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_catalog_attributes():
    response = client.get("/api/catalog/attributes")
    assert response.status_code == 200
    data = response.json()
    assert data["base_price"] == 185000.0
    assert "bunga_utama" in data["categories"]
    assert "bahan_wrap" in data["categories"]
    assert "gaya_rangkaian" in data["categories"]
    assert "ukuran" in data["categories"]
    assert len(data["categories"]["bunga_utama"]) >= 3


def test_special_recommendation():
    response = client.get("/api/catalog/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["has_recommendation"] is True
    assert len(data["items"]) == 4
    assert data["lift"] > 1.0


def test_customer_auth_and_order_flow():
    # 1. Customer Login / Register
    login_res = client.post(
        "/api/auth/login",
        json={"name": "Test Pelanggan Baru", "phone_number": "08999998888"},
    )
    assert login_res.status_code == 200
    user_data = login_res.json()["user"]
    user_id = user_data["id"]
    assert user_data["name"] == "Test Pelanggan Baru"

    # 2. Get Attributes to create order
    cat_res = client.get("/api/catalog/attributes")
    categories = cat_res.json()["categories"]

    attr_bunga = categories["bunga_utama"][0]["id"]
    attr_wrap = categories["bahan_wrap"][0]["id"]
    attr_gaya = categories["gaya_rangkaian"][0]["id"]
    attr_ukuran = categories["ukuran"][0]["id"]

    order_payload = {
        "user_id": user_id,
        "attribute_ids": [attr_bunga, attr_wrap, attr_gaya, attr_ukuran],
        "pickup_date": "2026-11-20",
        "pickup_time_slot": "09:00 - 10:00 WIB",
        "card_theme": "Birthday",
        "card_message": "Happy Birthday test!",
        "points_to_use": 0,
    }

    # 3. Create Order
    order_res = client.post("/api/orders", json=order_payload)
    assert order_res.status_code == 200
    order_data = order_res.json()["order"]
    order_id = order_data["id"]
    assert order_data["status"] == "Menunggu"

    # 4. Admin updates status to 'Diproses'
    from urllib.parse import quote
    enc_id = quote(order_id)
    status1_res = client.patch(f"/api/orders/{enc_id}/status", json={"status": "Diproses"})
    assert status1_res.status_code == 200
    assert status1_res.json()["order"]["status"] == "Diproses"

    # 5. Admin updates status to 'Selesai' (triggers points and RFM)
    status2_res = client.patch(f"/api/orders/{enc_id}/status", json={"status": "Selesai"})
    assert status2_res.status_code == 200
    assert status2_res.json()["order"]["status"] == "Selesai"
    assert status2_res.json()["order"]["customer_points"] > 0

    # 6. Check Loyalty Status
    loyalty_res = client.get(f"/api/loyalty/status/{user_id}")
    assert loyalty_res.status_code == 200
    loyalty = loyalty_res.json()
    assert loyalty["total_points"] > 0
    assert loyalty["total_completed_orders"] == 1


def test_invalid_order_rejection():
    # Missing 4 dimensions (only 2 sent)
    bad_res = client.post(
        "/api/orders",
        json={
            "user_id": 1,
            "attribute_ids": [1, 2],
            "pickup_date": "2026-11-20",
            "pickup_time_slot": "09:00 - 10:00 WIB",
        },
    )
    assert bad_res.status_code == 422  # validation error


def test_export_endpoints():
    # K-Means export
    res_kmeans = client.get("/api/export/kmeans")
    assert res_kmeans.status_code == 200
    assert "Customer_ID,Nama_Pelanggan,Recency_Days,Frequency_Count,Monetary_Value" in res_kmeans.text

    # FP-Growth export
    res_fpgrowth = client.get("/api/export/fpgrowth")
    assert res_fpgrowth.status_code == 200
    assert "Transaction_ID,Itemsets" in res_fpgrowth.text


def test_analytics_summary():
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "kmeans" in data
    assert "fp_growth" in data
    assert data["kmeans"]["silhouette_score"] > 0
    assert len(data["kmeans"]["clusters"]) == 3
    assert data["fp_growth"]["total_rules"] > 0


if __name__ == "__main__":
    print("Running integration tests...")
    test_health_check()
    print("✓ Health check passed")
    test_catalog_attributes()
    print("✓ Catalog attributes passed")
    test_special_recommendation()
    print("✓ Special recommendations passed")
    test_customer_auth_and_order_flow()
    print("✓ Customer auth & order flow passed")
    test_invalid_order_rejection()
    print("✓ Invalid order rejection passed")
    test_export_endpoints()
    print("✓ CSV export endpoints passed")
    test_analytics_summary()
    print("✓ Analytics summary passed")
    print("\nALL INTEGRATION TESTS PASSED!")
