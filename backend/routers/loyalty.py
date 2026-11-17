"""
Sreang Club Loyalty Router.
Provides membership status, K-Means determined tier pass, perks, and progress bars.
"""

from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from typing import Dict, Any

from backend.database import get_db

router = APIRouter(prefix="/api/loyalty", tags=["Sreang Club Loyalty"])

TIER_CONFIG = {
    "Gold Tier": {
        "title": "Gold Atelier Member",
        "badge_color": "from-amber-400 to-yellow-600",
        "icon": "✨",
        "description": "Pelanggan VIP Utama dengan frekuensi & loyalitas tertinggi.",
        "perks": [
            "Prioritas utama antrean perangkaian buket bunga segar",
            "Gratis Wax Seal & Pita Satin Premium untuk setiap pesanan",
            "Akses eksklusif koleksi bunga impor edisi terbatas",
            "Hadiah buket ulang tahun spesial dari Atelier",
        ],
        "reward_target_points": 200,
    },
    "Silver Tier": {
        "title": "Silver Bloom Member",
        "badge_color": "from-slate-300 to-slate-500",
        "icon": "🌿",
        "description": "Pelanggan setia dengan riwayat pemesanan aktif.",
        "perks": [
            "Gratis Kartu Ucapan Custom & Foto Polaroid mini",
            "Voucher potongan Rp 25.000 setiap kelipatan 50 poin",
            "Pemberitahuan awal untuk slot tanggal Valentine & Mother's Day",
        ],
        "reward_target_points": 100,
    },
    "Bronze Tier": {
        "title": "Bronze Petal Member",
        "badge_color": "from-amber-700 to-amber-900",
        "icon": "🌸",
        "description": "Anggota baru Sreang Florist Club.",
        "perks": [
            "Akumulasi 1 poin untuk setiap transaksi Rp 10.000",
            "Tukar poin untuk potongan belanja langsung",
            "Konsultasi gratis panduan perawatan kesegaran bunga",
        ],
        "reward_target_points": 50,
    },
}


@router.get("/status/{user_id}")
def get_loyalty_status(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    """
    Returns Sreang Club membership pass details for customer.
    """
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan.")

    tier = user["tier_status"] or "Bronze Tier"
    tier_info = TIER_CONFIG.get(tier, TIER_CONFIG["Bronze Tier"])

    # Fetch customer order summary
    cursor.execute(
        """
        SELECT COUNT(id) as total_orders, COALESCE(SUM(total_price), 0.0) as total_spent
        FROM orders
        WHERE user_id = ? AND status = 'Selesai'
        """,
        (user_id,),
    )
    order_stats = cursor.fetchone()

    # Fetch 3 recent orders
    cursor.execute(
        """
        SELECT id, pickup_date, pickup_time_slot, total_price, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 3
        """,
        (user_id,),
    )
    recent_orders = [dict(r) for r in cursor.fetchall()]

    points = user["total_points"]
    target = tier_info["reward_target_points"]
    progress_pct = min(100.0, round((points / target) * 100, 1)) if target > 0 else 100.0

    return {
        "user_id": user["id"],
        "name": user["name"],
        "phone_number": user["phone_number"],
        "tier": tier,
        "tier_title": tier_info["title"],
        "badge_color": tier_info["badge_color"],
        "icon": tier_info["icon"],
        "description": tier_info["description"],
        "perks": tier_info["perks"],
        "total_points": points,
        "reward_target_points": target,
        "progress_percentage": progress_pct,
        "total_completed_orders": order_stats["total_orders"],
        "total_spent_rp": order_stats["total_spent"],
        "recent_orders": recent_orders,
    }
