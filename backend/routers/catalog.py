"""
Catalog & Atelier Studio Router for Sreang Florist.
Handles 4-dimension bouquet components, inventory, and FP-Growth recommendations.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import sqlite3
from typing import Dict, List, Any, Optional

from backend.database import get_db
from backend.analytics.fp_growth import get_association_recommendations

router = APIRouter(prefix="/api/catalog", tags=["Catalog & Atelier"])

BASE_BOUQUET_PRICE = 185000.0


class AttributeUpdateRequest(BaseModel):
    stock: Optional[int] = Field(None, ge=0)
    price_modifier: Optional[float] = Field(None, ge=0.0)
    is_active: Optional[int] = Field(None, ge=0, le=1)


class AttributeCreateRequest(BaseModel):
    category: str = Field(..., pattern=r"^(bunga_utama|bahan_wrap|gaya_rangkaian|ukuran)$")
    name: str = Field(..., min_length=2, max_length=150)
    price_modifier: float = Field(0.0, ge=0.0)
    stock: int = Field(0, ge=0)


@router.get("/attributes")
def get_catalog_attributes(db: sqlite3.Connection = Depends(get_db)):
    """
    Returns all master attributes grouped by category for the Atelier Crafting Studio.
    """
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, category, name, price_modifier, stock, is_active
        FROM master_attributes
        WHERE is_active = 1
        ORDER BY id ASC
        """
    )
    rows = cursor.fetchall()

    grouped: Dict[str, List[Dict[str, Any]]] = {
        "bunga_utama": [],
        "bahan_wrap": [],
        "gaya_rangkaian": [],
        "ukuran": [],
    }

    for row in rows:
        cat = row["category"]
        if cat in grouped:
            grouped[cat].append({
                "id": row["id"],
                "name": row["name"],
                "price_modifier": row["price_modifier"],
                "stock": row["stock"],
                "is_active": row["is_active"],
            })

    return {
        "base_price": BASE_BOUQUET_PRICE,
        "categories": grouped,
        "total_active_components": len(rows),
    }


@router.get("/recommendations")
def get_special_recommendations(db: sqlite3.Connection = Depends(get_db)):
    """
    Returns FP-Growth powered 'Rekomendasi Spesial Untuk Anda' for the customer catalog.
    """
    recommendation = get_association_recommendations(db)
    return recommendation


@router.get("/all-attributes")
def get_all_attributes_for_admin(db: sqlite3.Connection = Depends(get_db)):
    """
    Returns all attributes including inactive and low-stock items for Admin inventory.
    """
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, category, name, price_modifier, stock, is_active, created_at
        FROM master_attributes
        ORDER BY category ASC, id ASC
        """
    )
    rows = cursor.fetchall()
    return [dict(r) for r in rows]


@router.patch("/attributes/{attr_id}")
def update_attribute(attr_id: int, payload: AttributeUpdateRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Admin endpoint to update component stock, price, or active status.
    """
    cursor = db.cursor()
    cursor.execute("SELECT * FROM master_attributes WHERE id = ?", (attr_id,))
    attr = cursor.fetchone()
    if not attr:
        raise HTTPException(status_code=404, detail="Komponen atribut tidak ditemukan.")

    updates = []
    values = []

    if payload.stock is not None:
        updates.append("stock = ?")
        values.append(payload.stock)
    if payload.price_modifier is not None:
        updates.append("price_modifier = ?")
        values.append(payload.price_modifier)
    if payload.is_active is not None:
        updates.append("is_active = ?")
        values.append(payload.is_active)

    if not updates:
        return {"success": True, "message": "Tidak ada perubahan data."}

    values.append(attr_id)
    query = f"UPDATE master_attributes SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, tuple(values))
    db.commit()

    cursor.execute("SELECT * FROM master_attributes WHERE id = ?", (attr_id,))
    updated = cursor.fetchone()
    return {
        "success": True,
        "message": f"Komponen '{updated['name']}' berhasil diperbarui.",
        "attribute": dict(updated),
    }
