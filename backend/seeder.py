"""
Database Seeder for Sreang Florist.
Seeds Master Attributes, Admin User, Customer Accounts, and 40 Realistic Transactions.
Designed to generate rich datasets for:
1. FP-Growth Association Rule Mining (4-attribute itemsets with clear frequent patterns)
2. K-Means RFM Customer Segmentation (distinct Recency, Frequency, and Monetary clusters)
"""

import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database import DB_PATH, get_db_connection, init_db

# 1. Master Attributes Definition
MASTER_ATTRIBUTES = [
    # Bunga Utama
    {"category": "bunga_utama", "name": "Mawar Merah Holland", "price_modifier": 20000.0, "stock": 45},
    {"category": "bunga_utama", "name": "Krisan Kuning Pompon", "price_modifier": 0.0, "stock": 60},
    {"category": "bunga_utama", "name": "Baby's Breath", "price_modifier": 35000.0, "stock": 30},
    # Bahan Wrap
    {"category": "bahan_wrap", "name": "Cellophane Matte Transparan", "price_modifier": 0.0, "stock": 50},
    {"category": "bahan_wrap", "name": "Spunbond Tebal Waterproof", "price_modifier": 0.0, "stock": 40},
    # Gaya Rangkaian
    {"category": "gaya_rangkaian", "name": "Korean Style Wrapping", "price_modifier": 0.0, "stock": 999},
    {"category": "gaya_rangkaian", "name": "Classic Round Spiral", "price_modifier": 0.0, "stock": 999},
    # Ukuran / Kuantitas Tangkai
    {"category": "ukuran", "name": "Standard (10 Tangkai)", "price_modifier": 0.0, "stock": 999},
    {"category": "ukuran", "name": "Deluxe (18 Tangkai)", "price_modifier": 65000.0, "stock": 999},
    {"category": "ukuran", "name": "Grandeur (25 Tangkai)", "price_modifier": 120000.0, "stock": 999},
]

# 2. Customer Profiles for Realistic RFM Clustering
CUSTOMERS = [
    {"name": "Siti Rahmawati", "phone": "081234567890", "tier": "Gold Tier"},
    {"name": "Budi Santoso", "phone": "081298765432", "tier": "Gold Tier"},
    {"name": "Dewi Lestari", "phone": "081311223344", "tier": "Silver Tier"},
    {"name": "Reza Pratama", "phone": "081355667788", "tier": "Silver Tier"},
    {"name": "Anisa Putri", "phone": "081223344556", "tier": "Silver Tier"},
    {"name": "Fajar Nugraha", "phone": "081334455667", "tier": "Bronze Tier"},
    {"name": "Maya Indah", "phone": "081245566778", "tier": "Bronze Tier"},
    {"name": "Dimas Anggara", "phone": "081356677889", "tier": "Bronze Tier"},
    {"name": "Nadia Safitri", "phone": "081267788990", "tier": "Bronze Tier"},
    {"name": "Kevin Sanjaya", "phone": "081378899001", "tier": "Bronze Tier"},
    {"name": "Clarissa Wijaya", "phone": "081289900112", "tier": "Bronze Tier"},
    {"name": "Rian Hidayat", "phone": "081390011223", "tier": "Bronze Tier"},
    {"name": "Jessica Tan", "phone": "081201122334", "tier": "Bronze Tier"},
]

TIME_SLOTS = [
    "09:00 - 10:00 WIB",
    "11:00 - 12:00 WIB",
    "16:00 - 17:00 WIB",
]

CARD_THEMES_MESSAGES = [
    ("Anniversary", "Selamat hari jadi yang ke-3, sayang! Semoga cinta kita selalu mekar abadi."),
    ("Birthday", "Happy 24th Birthday, Clarissa! Semoga harimu seindah bunga-bunga ini."),
    ("Graduation", "Congratulations on your Bachelor Degree, S.Kom! Proud of your hard work!"),
    ("Romantic", "Just because I love you today and always. From your secret admirer."),
    ("Congratulations", "Selamat atas pembukaan cabang baru! Semoga sukses dan berkah selalu."),
    ("Valentine", "To my one and only, Happy Valentine's Day. You are my blooming joy."),
]


def seed_database(reset: bool = True) -> None:
    """
    Seeds the SQLite database with initial master data and 40 dummy orders.
    """
    if reset and DB_PATH.exists():
        os.remove(DB_PATH)

    print(f"Creating database schema at: {DB_PATH}")
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Insert Master Attributes
    print("Seeding master attributes...")
    attr_id_map = {}
    for attr in MASTER_ATTRIBUTES:
        cursor.execute(
            """
            INSERT INTO master_attributes (category, name, price_modifier, stock, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (attr["category"], attr["name"], attr["price_modifier"], attr["stock"]),
        )
        attr_id_map[attr["name"]] = cursor.lastrowid

    # 2. Insert Admin User
    print("Seeding admin user...")
    cursor.execute(
        """
        INSERT INTO users (role, phone_number, name, pin_code, total_points, tier_status)
        VALUES ('admin', '0000000000', 'Admin Sreang TA', '123456', 0, 'System Admin')
        """
    )

    # 3. Insert Customers
    print(f"Seeding {len(CUSTOMERS)} customer profiles...")
    user_id_map = {}
    for cust in CUSTOMERS:
        cursor.execute(
            """
            INSERT INTO users (role, phone_number, name, pin_code, total_points, tier_status)
            VALUES ('customer', ?, ?, NULL, 0, ?)
            """,
            (cust["phone"], cust["name"], cust["tier"]),
        )
        user_id_map[cust["phone"]] = cursor.lastrowid

    # 4. Generate 40 Dummy Orders with Clear FP-Growth Patterns and RFM Spanning
    # Reference Date: 2026-11-17 (current local date)
    ref_date = datetime(2026, 11, 17, 10, 0, 0)

    # Itemset archetype definitions for FP-Growth
    pattern_a = [
        "Mawar Merah Holland",
        "Cellophane Matte Transparan",
        "Korean Style Wrapping",
        "Standard (10 Tangkai)",
    ]  # Archetype A (Best Seller: 16 orders)
    pattern_b = [
        "Baby's Breath",
        "Cellophane Matte Transparan",
        "Korean Style Wrapping",
        "Deluxe (18 Tangkai)",
    ]  # Archetype B (Luxury Floral: 10 orders)
    pattern_c = [
        "Krisan Kuning Pompon",
        "Spunbond Tebal Waterproof",
        "Classic Round Spiral",
        "Standard (10 Tangkai)",
    ]  # Archetype C (Warm Bouquet: 8 orders)
    pattern_d = [
        "Mawar Merah Holland",
        "Spunbond Tebal Waterproof",
        "Korean Style Wrapping",
        "Grandeur (25 Tangkai)",
    ]  # Archetype D (Grand Romance: 4 orders)
    pattern_e = [
        "Baby's Breath",
        "Spunbond Tebal Waterproof",
        "Classic Round Spiral",
        "Standard (10 Tangkai)",
    ]  # Archetype E (Occasional Mix: 2 orders)

    # Allocation of patterns across 40 orders
    # Total: 16 + 10 + 8 + 4 + 2 = 40 orders
    order_blueprints = (
        [pattern_a] * 16
        + [pattern_b] * 10
        + [pattern_c] * 8
        + [pattern_d] * 4
        + [pattern_e] * 2
    )
    # Shuffle predictably
    rng = random.Random(42)
    rng.shuffle(order_blueprints)

    # Customer assignment plan (RFM distribution)
    # Customer 0 (Siti): 6 orders (Recency: 2, 7, 15, 23, 31, 45 days ago) -> High RFM
    # Customer 1 (Budi): 5 orders (Recency: 4, 11, 19, 28, 40 days ago) -> High RFM
    # Customer 2 (Dewi): 4 orders (Recency: 6, 14, 25, 38 days ago) -> Mid RFM
    # Customer 3 (Reza): 4 orders (Recency: 8, 16, 27, 42 days ago) -> Mid RFM
    # Customer 4 (Anisa): 3 orders (Recency: 10, 21, 35 days ago) -> Mid RFM
    # Customer 5 (Fajar): 3 orders (Recency: 12, 24, 39 days ago)
    # Customer 6 (Maya): 3 orders (Recency: 15, 29, 44 days ago)
    # Customer 7 (Dimas): 3 orders (Recency: 18, 33, 48 days ago)
    # Customer 8 (Nadia): 2 orders (Recency: 22, 50 days ago)
    # Customer 9 (Kevin): 2 orders (Recency: 26, 52 days ago)
    # Customer 10 (Clarissa): 2 orders (Recency: 30, 56 days ago)
    # Customer 11 (Rian): 2 orders (Recency: 35, 60 days ago)
    # Customer 12 (Jessica): 1 order (Recency: 1 day ago, 'Menunggu')
    # Total orders = 6 + 5 + 4 + 4 + 3 + 3 + 3 + 3 + 2 + 2 + 2 + 2 + 1 = 40 orders!

    customer_order_schedules = [
        ("081234567890", [2, 7, 15, 23, 31, 45]),
        ("081298765432", [4, 11, 19, 28, 40]),
        ("081311223344", [6, 14, 25, 38]),
        ("081355667788", [8, 16, 27, 42]),
        ("081223344556", [10, 21, 35]),
        ("081334455667", [12, 24, 39]),
        ("081245566778", [15, 29, 44]),
        ("081356677889", [18, 33, 48]),
        ("081267788990", [22, 50]),
        ("081378899001", [26, 52]),
        ("081289900112", [30, 56]),
        ("081390011223", [35, 60]),
        ("081201122334", [1]),
    ]

    orders_data = []
    order_idx = 0
    for phone, days_ago_list in customer_order_schedules:
        for days_ago in days_ago_list:
            orders_data.append((phone, days_ago, order_blueprints[order_idx]))
            order_idx += 1

    # Sort orders chronologically by date
    orders_data.sort(key=lambda x: x[1], reverse=True)

    print(f"Seeding {len(orders_data)} orders and customizations...")
    base_price = 185000.0
    accumulated_points_by_user = {}

    for i, (phone, days_ago, itemset) in enumerate(orders_data, start=1):
        order_id = f"#SRG-{1000 + i}"
        user_id = user_id_map[phone]

        # Order creation date & pickup date
        created_time = ref_date - timedelta(days=days_ago, hours=rng.randint(1, 4))
        pickup_time = ref_date - timedelta(days=days_ago - 1 if days_ago > 0 else 0)
        pickup_date_str = pickup_time.strftime("%Y-%m-%d")
        created_at_str = created_time.strftime("%Y-%m-%d %H:%M:%S")

        # Determine order status:
        # Most are 'Selesai' (36 orders), latest ones can be 'Diproses' (2) or 'Menunggu' (2)
        if days_ago <= 1 and phone == "081201122334":
            status = "Menunggu"
        elif days_ago <= 2 and i == 40:
            status = "Menunggu"
        elif days_ago <= 4 and i in (38, 39):
            status = "Diproses"
        else:
            status = "Selesai"

        # Calculate total price
        modifier_sum = 0.0
        for item_name in itemset:
            matching_attr = next(a for a in MASTER_ATTRIBUTES if a["name"] == item_name)
            modifier_sum += matching_attr["price_modifier"]
        total_price = base_price + modifier_sum

        # Points
        points_earned = int(total_price / 10000) if status == "Selesai" else 0
        points_used = 0

        # Card theme and message
        theme, msg = rng.choice(CARD_THEMES_MESSAGES)
        time_slot = rng.choice(TIME_SLOTS)

        cursor.execute(
            """
            INSERT INTO orders (
                id, user_id, pickup_date, pickup_time_slot,
                card_theme, card_message, base_price,
                points_used, points_earned, total_price,
                status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                user_id,
                pickup_date_str,
                time_slot,
                theme,
                msg,
                base_price,
                points_used,
                points_earned,
                total_price,
                status,
                created_at_str,
            ),
        )

        # Insert customizations
        for item_name in itemset:
            attr_id = attr_id_map[item_name]
            cursor.execute(
                """
                INSERT INTO order_customizations (order_id, attribute_id)
                VALUES (?, ?)
                """,
                (order_id, attr_id),
            )

        # Accumulate points for customer if Selesai
        if status == "Selesai":
            accumulated_points_by_user[user_id] = (
                accumulated_points_by_user.get(user_id, 0) + points_earned
            )

    # Update users total_points based on completed orders
    for user_id, points in accumulated_points_by_user.items():
        cursor.execute(
            "UPDATE users SET total_points = ? WHERE id = ?",
            (points, user_id),
        )

    conn.commit()
    conn.close()

    print(f"Successfully seeded database at {DB_PATH}")
    print(f"  - Master Attributes: {len(MASTER_ATTRIBUTES)}")
    print(f"  - Users: {len(CUSTOMERS) + 1} (1 Admin, {len(CUSTOMERS)} Customers)")
    print(f"  - Orders: {len(orders_data)} orders")
    print(f"  - Customizations: {len(orders_data) * 4} items linked")


if __name__ == "__main__":
    seed_database()
