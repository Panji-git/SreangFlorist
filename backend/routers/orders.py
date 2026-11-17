"""
Orders Router for Sreang Florist.
Handles order checkout, 4-dimension validation, scheduling, status management,
and points/tier triggers.
"""

from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import random
import sqlite3
import string
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.analytics.rfm_kmeans import segment_customers_and_update

router = APIRouter(prefix="/api/orders", tags=["Orders & Scheduling"])

BASE_PRICE = 185000.0
VALID_TIME_SLOTS = [
    "09:00 - 10:00 WIB",
    "11:00 - 12:00 WIB",
    "16:00 - 17:00 WIB",
]
VALID_STATUSES = ["Menunggu", "Diproses", "Selesai", "Dibatalkan"]
REQUIRED_CATEGORIES = {"bunga_utama", "bahan_wrap", "gaya_rangkaian", "ukuran"}


class CreateOrderRequest(BaseModel):
    user_id: int
    attribute_ids: List[int] = Field(..., min_length=4, max_length=4)
    pickup_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    pickup_time_slot: str
    card_theme: Optional[str] = None
    card_message: Optional[str] = None
    points_to_use: int = Field(0, ge=0)


class UpdateOrderStatusRequest(BaseModel):
    status: str


def generate_order_id(db: sqlite3.Connection) -> str:
    """Generates unique sequential order ID, e.g. #SRG-1041."""
    cursor = db.cursor()
    cursor.execute("SELECT id FROM orders WHERE id LIKE '#SRG-%' ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()

    max_num = 1040
    for r in rows:
        order_str = r["id"].replace("#SRG-", "")
        if order_str.isdigit():
            val = int(order_str)
            if val > max_num:
                max_num = val

    next_num = max_num + 1
    return f"#SRG-{next_num}"


@router.post("")
def create_order(payload: CreateOrderRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Creates a new custom bouquet order with 4-dimension customization validation.
    """
    cursor = db.cursor()

    # 1. Validate User
    cursor.execute("SELECT * FROM users WHERE id = ?", (payload.user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan.")

    # 2. Validate Time Slot
    if payload.pickup_time_slot not in VALID_TIME_SLOTS:
        raise HTTPException(
            status_code=400,
            detail=f"Slot waktu tidak valid. Pilihan: {', '.join(VALID_TIME_SLOTS)}",
        )

    # 3. Validate Attributes (exactly 4 dimensions)
    placeholder = ",".join(["?"] * len(payload.attribute_ids))
    cursor.execute(
        f"SELECT * FROM master_attributes WHERE id IN ({placeholder}) AND is_active = 1",
        tuple(payload.attribute_ids),
    )
    attributes = cursor.fetchall()

    if len(attributes) != 4:
        raise HTTPException(
            status_code=400,
            detail="Pilihan komponen harus memuat 4 atribut aktif yang valid.",
        )

    categories_present = {a["category"] for a in attributes}
    if categories_present != REQUIRED_CATEGORIES:
        missing = REQUIRED_CATEGORIES - categories_present
        raise HTTPException(
            status_code=400,
            detail=f"Kustomisasi belum lengkap. Harap pilih satu item dari setiap kategori. Kurang: {', '.join(missing)}",
        )

    # 4. Check Stock and Calculate Price
    modifiers_sum = 0.0
    for a in attributes:
        if a["stock"] <= 0 and a["category"] in ("bunga_utama", "bahan_wrap"):
            raise HTTPException(
                status_code=400,
                detail=f"Maaf, stok komponen '{a['name']}' sedang habis.",
            )
        modifiers_sum += a["price_modifier"]

    total_price = BASE_PRICE + modifiers_sum

    # Handle points discount (1 point = Rp 100 max up to 50% order)
    points_used = 0
    if payload.points_to_use > 0:
        available_points = user["total_points"]
        points_used = min(payload.points_to_use, available_points)
        discount = points_used * 100.0
        total_price = max(0.0, total_price - discount)

    order_id = generate_order_id(db)
    points_earned = int(total_price / 10000)

    # Deduct used points immediately if any
    if points_used > 0:
        cursor.execute(
            "UPDATE users SET total_points = total_points - ? WHERE id = ?",
            (points_used, user["id"]),
        )

    # Decrement stock for limited items
    for a in attributes:
        if a["stock"] < 999:
            cursor.execute(
                "UPDATE master_attributes SET stock = stock - 1 WHERE id = ?",
                (a["id"],),
            )

    # Insert Order
    cursor.execute(
        """
        INSERT INTO orders (
            id, user_id, pickup_date, pickup_time_slot,
            card_theme, card_message, base_price,
            points_used, points_earned, total_price,
            status, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Menunggu', CURRENT_TIMESTAMP)
        """,
        (
            order_id,
            user["id"],
            payload.pickup_date,
            payload.pickup_time_slot,
            payload.card_theme or "General",
            payload.card_message or "",
            BASE_PRICE,
            points_used,
            points_earned,
            total_price,
        ),
    )

    # Insert Order Customizations
    for a in attributes:
        cursor.execute(
            """
            INSERT INTO order_customizations (order_id, attribute_id)
            VALUES (?, ?)
            """,
            (order_id, a["id"]),
        )

    db.commit()

    return {
        "success": True,
        "message": f"Pesanan {order_id} berhasil dibuat.",
        "order": {
            "id": order_id,
            "user_name": user["name"],
            "pickup_date": payload.pickup_date,
            "pickup_time_slot": payload.pickup_time_slot,
            "total_price": total_price,
            "points_earned": points_earned,
            "status": "Menunggu",
            "attributes": [
                {"id": a["id"], "name": a["name"], "category": a["category"]}
                for a in attributes
            ],
        },
    }


@router.get("")
def list_orders(
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    List orders with customer names and attribute summaries.
    Filterable by user_id or status.
    """
    cursor = db.cursor()
    query = """
        SELECT 
            o.id, o.user_id, u.name as customer_name, u.phone_number,
            o.pickup_date, o.pickup_time_slot, o.card_theme, o.card_message,
            o.base_price, o.points_used, o.points_earned, o.total_price,
            o.status, o.created_at,
            GROUP_CONCAT(ma.name, ' | ') as components
        FROM orders o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN order_customizations oc ON o.id = oc.order_id
        LEFT JOIN master_attributes ma ON oc.attribute_id = ma.id
        WHERE 1=1
    """
    params = []
    if user_id:
        query += " AND o.user_id = ?"
        params.append(user_id)
    if status:
        query += " AND o.status = ?"
        params.append(status)

    query += " GROUP BY o.id ORDER BY o.created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


@router.get("/{order_id}")
def get_order_detail(order_id: str, db: sqlite3.Connection = Depends(get_db)):
    """
    Retrieves full details of a single order including all chosen components.
    """
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT 
            o.*, u.name as customer_name, u.phone_number as customer_phone
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
        """,
        (order_id,),
    )
    order = cursor.fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")

    cursor.execute(
        """
        SELECT ma.id, ma.category, ma.name, ma.price_modifier
        FROM order_customizations oc
        JOIN master_attributes ma ON oc.attribute_id = ma.id
        WHERE oc.order_id = ?
        """,
        (order_id,),
    )
    components = [dict(c) for c in cursor.fetchall()]

    result = dict(order)
    result["components"] = components
    return result


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: UpdateOrderStatusRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Admin updates order status ('Menunggu' -> 'Diproses' -> 'Selesai' / 'Dibatalkan').
    Transition to 'Selesai' triggers points injection and RFM re-clustering.
    """
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Status tidak valid. Pilihan: {', '.join(VALID_STATUSES)}",
        )

    cursor = db.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan.")

    old_status = order["status"]
    new_status = payload.status

    cursor.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (new_status, order_id),
    )
    db.commit()

    # If completed, re-run customer RFM segmentation to update tiers automatically
    kmeans_result = None
    if new_status == "Selesai" and old_status != "Selesai":
        try:
            kmeans_result = segment_customers_and_update(db)
        except Exception as e:
            print("RFM update notice:", e)

    cursor.execute(
        """
        SELECT o.*, u.name as customer_name, u.total_points as customer_points, u.tier_status as customer_tier
        FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.id = ?
        """,
        (order_id,),
    )
    updated = cursor.fetchone()

    return {
        "success": True,
        "message": f"Status pesanan {order_id} berhasil diubah menjadi '{new_status}'.",
        "order": dict(updated),
        "kmeans_recalculated": kmeans_result is not None,
    }
