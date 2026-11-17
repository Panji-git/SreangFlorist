"""
Authentication Router for Sreang Florist.
Supports quick customer login (Phone & Name) and Admin portal PIN authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import sqlite3
from typing import Optional

from backend.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class CustomerLoginRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=8, max_length=20)


class AdminLoginRequest(BaseModel):
    identifier: str = Field(..., description="Admin Email or Phone")
    pin_code: str = Field(..., min_length=4, max_length=10)


@router.post("/login")
def customer_login(payload: CustomerLoginRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Fast customer login/registration by phone number and name.
    If the phone number doesn't exist yet, a new customer account is created automatically.
    """
    clean_phone = payload.phone_number.strip().replace(" ", "").replace("-", "")
    clean_name = payload.name.strip()

    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE phone_number = ?", (clean_phone,))
    user = cursor.fetchone()

    if user:
        # Existing user - optionally update name if provided and not blank
        if clean_name and user["name"] != clean_name and user["role"] == "customer":
            cursor.execute(
                "UPDATE users SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (clean_name, user["id"]),
            )
            db.commit()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user["id"],))
            user = cursor.fetchone()
    else:
        # New customer registration
        cursor.execute(
            """
            INSERT INTO users (role, phone_number, name, pin_code, total_points, tier_status)
            VALUES ('customer', ?, ?, NULL, 0, 'Bronze Tier')
            """,
            (clean_phone, clean_name),
        )
        db.commit()
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE id = ?", (new_id,))
        user = cursor.fetchone()

    return {
        "success": True,
        "message": "Login berhasil.",
        "user": {
            "id": user["id"],
            "role": user["role"],
            "phone_number": user["phone_number"],
            "name": user["name"],
            "total_points": user["total_points"],
            "tier_status": user["tier_status"],
        },
    }


@router.post("/admin-login")
def admin_login(payload: AdminLoginRequest, db: sqlite3.Connection = Depends(get_db)):
    """
    Admin portal authentication with PIN Code.
    """
    clean_id = payload.identifier.strip()
    clean_pin = payload.pin_code.strip()

    cursor = db.cursor()
    # Check if admin matches by phone_number or PIN
    cursor.execute(
        "SELECT * FROM users WHERE role = 'admin' AND pin_code = ?",
        (clean_pin,),
    )
    admin = cursor.fetchone()

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kredensial Admin atau PIN salah.",
        )

    return {
        "success": True,
        "message": "Autentikasi Admin berhasil.",
        "admin": {
            "id": admin["id"],
            "role": "admin",
            "name": admin["name"],
            "phone_number": admin["phone_number"],
            "tier_status": "System Administrator",
        },
    }


@router.get("/me")
def get_current_user_profile(user_id: Optional[int] = None, phone: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    """
    Retrieves the latest user profile and loyalty points.
    """
    if not user_id and not phone:
        raise HTTPException(status_code=400, detail="Harap sediakan user_id atau phone.")

    cursor = db.cursor()
    if user_id:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    else:
        cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone.strip(),))

    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")

    return {
        "id": user["id"],
        "role": user["role"],
        "name": user["name"],
        "phone_number": user["phone_number"],
        "total_points": user["total_points"],
        "tier_status": user["tier_status"],
    }
