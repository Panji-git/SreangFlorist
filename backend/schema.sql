-- Sreang Florist SQLite Schema
-- DDL & Triggers for Retail Analytics System (Tugas Akhir)

PRAGMA foreign_keys = ON;

-- 1. Tabel Pengguna (Pelanggan & Admin)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer', 'admin')),
    phone_number TEXT NOT NULL UNIQUE, -- Identitas utama pelanggan untuk RFM K-Means
    name TEXT NOT NULL,
    pin_code TEXT NULL, -- Khusus untuk otentikasi admin
    total_points INTEGER NOT NULL DEFAULT 0,
    tier_status TEXT NOT NULL DEFAULT 'Silver Tier', -- Label hasil klastering K-Means
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Master Atribut & Katalog
CREATE TABLE IF NOT EXISTS master_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK(category IN ('bunga_utama', 'bahan_wrap', 'gaya_rangkaian', 'ukuran')),
    name TEXT NOT NULL, -- Nama itemset untuk FP-Growth (cth: Mawar Merah Holland)
    price_modifier REAL NOT NULL DEFAULT 0.0,
    stock INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabel Transaksi & Pre-Order
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY, -- Format: #SRG-XXXX
    user_id INTEGER NOT NULL,
    pickup_date TEXT NOT NULL, -- Format ISO: YYYY-MM-DD
    pickup_time_slot TEXT NOT NULL CHECK(pickup_time_slot IN ('09:00 - 10:00 WIB', '11:00 - 12:00 WIB', '16:00 - 17:00 WIB')),
    card_theme TEXT NULL,
    card_message TEXT NULL,
    base_price REAL NOT NULL DEFAULT 185000.0,
    points_used INTEGER NOT NULL DEFAULT 0,
    points_earned INTEGER NOT NULL DEFAULT 0,
    total_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'Menunggu' CHECK(status IN ('Menunggu', 'Diproses', 'Selesai', 'Dibatalkan')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- 4. Tabel Detail Kustomisasi Pesanan (Pivot / Transaksional Itemset)
CREATE TABLE IF NOT EXISTS order_customizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    attribute_id INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (attribute_id) REFERENCES master_attributes(id) ON DELETE RESTRICT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_pickup_date ON orders(pickup_date);
CREATE INDEX IF NOT EXISTS idx_order_customizations_order_id ON order_customizations(order_id);
CREATE INDEX IF NOT EXISTS idx_order_customizations_attribute_id ON order_customizations(attribute_id);

-- Trigger untuk penambahan poin otomatis saat status pesanan menjadi 'Selesai'
CREATE TRIGGER IF NOT EXISTS after_order_completed
AFTER UPDATE OF status ON orders
FOR EACH ROW
WHEN NEW.status = 'Selesai' AND OLD.status != 'Selesai'
BEGIN
    UPDATE users 
    SET total_points = total_points + CAST(NEW.total_price / 10000 AS INTEGER),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.user_id;
END;
