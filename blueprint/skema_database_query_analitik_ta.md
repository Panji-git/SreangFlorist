# Skema Database (DDL SQLite / MySQL) & Query Ekstraksi Data TA

Dokumen ini berisi rancangan fisik basis data (*Relational Database*) untuk sistem **Sreang Florist** yang dioptimalkan untuk **SQLite** (dengan catatan kompatibilitas **MySQL**), serta *query* SQL yang dieksekusi oleh **FastAPI** untuk kalkulasi algoritma Python *native* dan ekspor dataset CSV ke **Google Colab**.

## 1. Entity Relationship Diagram (Konseptual Relasi)

* **`users` (1)** $\rightarrow$ **(N) `orders`**: Satu pelanggan (diidentifikasi unik melalui `phone_number`) dapat memiliki banyak riwayat pesanan.
* **`orders` (1)** $\rightarrow$ **(N) `order_customizations`**: Satu pesanan memuat rincian 4 atribut kustomisasi yang dipilih.
* **`master_attributes` (1)** $\rightarrow$ **(N) `order_customizations`**: Setiap atribut merujuk pada master data komponen untuk menjaga konsistensi penamaan (*data integrity*).

## 2. Data Definition Language (DDL SQLite)

Jalankan skrip SQL berikut untuk menginisialisasi file database SQLite Anda (misalnya: `sreang_florist.db`). Pastikan *Foreign Keys* diaktifkan pada setiap sesi koneksi Python (`cursor.execute("PRAGMA foreign_keys = ON;")`).

```sql
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
```

*(Catatan: Jika menggunakan **MySQL**, ganti `INTEGER PRIMARY KEY AUTOINCREMENT` menjadi `INT AUTO_INCREMENT PRIMARY KEY`, `TEXT` menjadi `VARCHAR`/`ENUM`, dan `REAL` menjadi `DECIMAL(10,2)`).*

## 3. Data Seeding (Contoh Data Awal)

Data awal untuk mengisi 4 kategori kustomisasi pada halaman katalog:

```sql
INSERT INTO master_attributes (category, name, price_modifier, stock) VALUES
('bunga_utama', 'Mawar Merah Holland', 20000.0, 45),
('bunga_utama', 'Krisan Kuning Pompon', 0.0, 60),
('bunga_utama', 'Baby''s Breath', 35000.0, 30),
('bahan_wrap', 'Cellophane Matte Transparan', 0.0, 12),
('bahan_wrap', 'Spunbond Tebal Waterproof', 0.0, 8),
('gaya_rangkaian', 'Korean Style Wrapping', 0.0, 999),
('gaya_rangkaian', 'Classic Round Spiral', 0.0, 999),
('ukuran', 'Standard (10 Tangkai)', 0.0, 999),
('ukuran', 'Deluxe (18 Tangkai)', 65000.0, 999),
('ukuran', 'Grandeur (25 Tangkai)', 120000.0, 999);

-- Seed Admin Default
INSERT INTO users (role, phone_number, name, pin_code, tier_status) VALUES
('admin', '0000000000', 'Admin Sreang TA', '123456', 'System Admin');
```

## 4. Query Ekstraksi Data (SQLite) untuk FastAPI & Google Colab

Query berikut dijalankan oleh *endpoint* FastAPI baik untuk diproses oleh fungsi Python *native* maupun diekspor menjadi file `.csv` untuk dianalisis di **Google Colab**.

### A. Query Ekspor Dataset K-Means (`kmeans_rfm.csv`)

Menggunakan fungsi `julianday()` bawaan SQLite untuk menghitung selisih hari (**Recency**), jumlah transaksi (**Frequency**), dan total belanja (**Monetary**) dari pesanan berstatus `'Selesai'`.

```sql
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
```

### B. Query Ekspor Dataset FP-Growth (`fp_growth.csv`)

Menggunakan `GROUP_CONCAT()` untuk menggabungkan atribut kustomisasi per transaksi menjadi satu baris *itemset* yang siap di-*parsing* di Python/Google Colab.

```sql
SELECT 
    o.id AS Transaction_ID,
    GROUP_CONCAT(ma.name, ', ') AS Itemsets
FROM orders o
JOIN order_customizations oc ON o.id = oc.order_id
JOIN master_attributes ma ON oc.attribute_id = ma.id
WHERE o.status = 'Selesai'
GROUP BY o.id;
```

## 5. Logika Penambahan Poin Otomatis (FastAPI / Trigger)

Dalam arsitektur FastAPI + SQLite, logika penambahan poin dapat ditangani langsung pada *endpoint* `PATCH /api/orders/{order_id}/status` maupun melalui *Trigger* SQLite berikut (kelipatan Rp 10.000 = 1 poin):

```sql
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
```