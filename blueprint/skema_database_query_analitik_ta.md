# Skema Database (DDL SQLite & Django ORM) & Query Ekstraksi Data TA

Dokumen ini berisi rancangan fisik basis data (*Relational Database*) untuk sistem **Sreang Florist** yang dioptimalkan untuk **SQLite lokal** (dengan pemetaan kelas model **Django ORM**), serta *query* SQL analitik yang dieksekusi oleh backend **Django REST Framework** untuk kalkulasi algoritma Python *native* dan ekspor dataset CSV ke **Google Colab**.

---

## 1. Entity Relationship Diagram (Konseptual Relasi)

* **`users` (1)** $\rightarrow$ **(N) `orders`**: Satu pelanggan (diidentifikasi unik melalui `username` dan `phone_number`) dapat memiliki banyak riwayat pesanan.
* **`orders` (1)** $\rightarrow$ **(N) `order_customizations`**: Satu pesanan memuat rincian 4 atribut kustomisasi buket yang dipilih.
* **`master_attributes` (1)** $\rightarrow$ **(N) `order_customizations`**: Setiap atribut kustomisasi merujuk pada master data komponen 4 dimensi untuk menjaga konsistensi penamaan (*data integrity*).

---

## 2. Data Definition Language (DDL SQLite) & Model Django ORM

### A. Skrip DDL SQLite Fisik (`sreang_florist.db` / `db.sqlite3`)

Pastikan *Foreign Keys* diaktifkan pada setiap sesi koneksi SQLite (`PRAGMA foreign_keys = ON;`).

```sql
PRAGMA foreign_keys = ON;

-- 1. Tabel Pengguna (Pelanggan & Admin)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer', 'admin')),
    username TEXT NOT NULL UNIQUE, -- Identitas login utama pelanggan
    phone_number TEXT NOT NULL UNIQUE, -- Identitas kontak/WhatsApp pelanggan untuk RFM K-Means
    name TEXT NOT NULL,
    pin_code TEXT NULL, -- Khusus untuk otentikasi portal admin
    total_points INTEGER NOT NULL DEFAULT 0,
    tier_status TEXT NOT NULL DEFAULT 'Bronze Tier', -- Label hasil klastering K-Means (Gold, Silver, Bronze)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabel Master Atribut & Komponen Katalog
CREATE TABLE IF NOT EXISTS master_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL CHECK(category IN ('bunga_utama', 'bahan_wrap', 'gaya_rangkaian', 'ukuran')),
    name TEXT NOT NULL, -- Nama komponen untuk itemset FP-Growth (cth: Mawar Merah Holland)
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

-- 4. Tabel Detail Kustomisasi Pesanan (Pivot Transaksional Itemset FP-Growth)
CREATE TABLE IF NOT EXISTS order_customizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    attribute_id INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (attribute_id) REFERENCES master_attributes(id) ON DELETE RESTRICT
);

-- Indeks Performa
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_pickup_date ON orders(pickup_date);
CREATE INDEX IF NOT EXISTS idx_order_customizations_order_id ON order_customizations(order_id);
CREATE INDEX IF NOT EXISTS idx_order_customizations_attr_id ON order_customizations(attribute_id);
```

---

### B. Definisi Model Django ORM (`models.py`)

Implementasi deklaratif di Django backend:

```python
from django.db import models

class User(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    username = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=25, unique=True)
    name = models.CharField(max_length=150)
    pin_code = models.CharField(max_length=20, null=True, blank=True)
    total_points = models.IntegerField(default=0)
    tier_status = models.CharField(max_length=50, default='Bronze Tier')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.name} (@{self.username})"


class MasterAttribute(models.Model):
    CATEGORY_CHOICES = (
        ('bunga_utama', 'Bunga Utama'),
        ('bahan_wrap', 'Bahan Wrap'),
        ('gaya_rangkaian', 'Gaya Rangkaian'),
        ('ukuran', 'Ukuran Tangkai'),
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=150)
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'master_attributes'

    def __str__(self):
        return f"{self.name} ({self.category})"


class Order(models.Model):
    STATUS_CHOICES = (
        ('Menunggu', 'Menunggu'),
        ('Diproses', 'Diproses'),
        ('Selesai', 'Selesai'),
        ('Dibatalkan', 'Dibatalkan'),
    )
    TIME_SLOT_CHOICES = (
        ('09:00 - 10:00 WIB', 'Pagi (09:00 - 10:00 WIB)'),
        ('11:00 - 12:00 WIB', 'Siang (11:00 - 12:00 WIB)'),
        ('16:00 - 17:00 WIB', 'Sore (16:00 - 17:00 WIB)'),
    )
    id = models.CharField(max_length=50, primary_key=True)  # Format: #SRG-XXXX
    user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='orders')
    pickup_date = models.DateField()
    pickup_time_slot = models.CharField(max_length=50, choices=TIME_SLOT_CHOICES)
    card_theme = models.CharField(max_length=100, null=True, blank=True)
    card_message = models.TextField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=185000.0)
    points_used = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Menunggu')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'


class OrderCustomization(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='customizations')
    attribute = models.ForeignKey(MasterAttribute, on_delete=models.RESTRICT, related_name='order_usages')

    class Meta:
        db_table = 'order_customizations'
```

---

## 3. Data Seeding (Data Inisialisasi Awal)

Data awal untuk mengisi komponen kustomisasi 4 dimensi dan akun admin pengelola:

```sql
INSERT INTO master_attributes (category, name, price_modifier, stock) VALUES
('bunga_utama', 'Mawar Merah Holland', 20000.0, 45),
('bunga_utama', 'Krisan Kuning Pompon', 0.0, 60),
('bunga_utama', 'Baby''s Breath', 35000.0, 30),
('bahan_wrap', 'Cellophane Matte Transparan', 0.0, 50),
('bahan_wrap', 'Spunbond Tebal Waterproof', 0.0, 40),
('gaya_rangkaian', 'Korean Style Wrapping', 0.0, 999),
('gaya_rangkaian', 'Classic Round Spiral', 0.0, 999),
('ukuran', 'Standard (10 Tangkai)', 0.0, 999),
('ukuran', 'Deluxe (18 Tangkai)', 65000.0, 999),
('ukuran', 'Grandeur (25 Tangkai)', 120000.0, 999);

-- Seed Akun Admin Default (dengan Username & Phone)
INSERT INTO users (role, username, phone_number, name, pin_code, tier_status) VALUES
('admin', 'admin_sreang', '0000000000', 'Admin Sreang TA', '123456', 'System Admin');
```

---

## 4. Query Ekstraksi Data (SQLite) untuk Django & Google Colab

Query SQL berikut dieksekusi oleh Django REST Framework untuk pemodelan algoritma in-app dan ekspor dataset `.csv` ke **Google Colab**.

### A. Query Ekspor Dataset K-Means RFM (`kmeans_rfm.csv`)
Menghitung selisih hari (**Recency**), jumlah transaksi (**Frequency**), dan total belanja (**Monetary**) dari pesanan berstatus `'Selesai'`:

```sql
SELECT 
    u.phone_number AS Customer_ID,
    u.username AS Username,
    u.name AS Nama_Pelanggan,
    CAST(julianday('now', 'localtime') - julianday(MAX(o.pickup_date)) AS INTEGER) AS Recency_Days,
    COUNT(o.id) AS Frequency_Count,
    SUM(o.total_price) AS Monetary_Value
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE u.role = 'customer' 
  AND o.status = 'Selesai'
GROUP BY u.id, u.phone_number, u.username, u.name
ORDER BY Monetary_Value DESC;
```

### B. Query Ekspor Dataset Asosiasi FP-Growth (`fp_growth.csv`)
Menggabungkan 4 atribut per transaksi menjadi satu baris *itemset*:

```sql
SELECT 
    o.id AS Transaction_ID,
    GROUP_CONCAT(ma.name, ', ') AS Itemsets
FROM orders o
JOIN order_customizations oc ON o.id = oc.order_id
JOIN master_attributes ma ON oc.attribute_id = ma.id
WHERE o.status = 'Selesai'
GROUP BY o.id
ORDER BY o.id ASC;
```

### C. Query Ekspor Riwayat Pesanan Lengkap (`riwayat_pesanan.csv`)
Mengekspor seluruh riwayat transaksi operasional untuk modul admin:

```sql
SELECT 
    o.id AS ID_Pesanan,
    u.id AS ID_Pelanggan,
    u.username AS Username,
    u.name AS Nama_Pelanggan,
    u.phone_number AS No_Telepon,
    o.pickup_date AS Tanggal_Pickup,
    o.pickup_time_slot AS Slot_Waktu,
    COALESCE(o.card_theme, '-') AS Tema_Kartu,
    COALESCE(o.card_message, '-') AS Pesan_Kartu,
    GROUP_CONCAT(ma.name, ' | ') AS Komponen_Buket,
    o.base_price AS Base_Price,
    o.points_used AS Poin_Digunakan,
    o.total_price AS Total_Harga,
    o.points_earned AS Poin_Didapat,
    o.status AS Status,
    o.created_at AS Tanggal_Dibuat
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_customizations oc ON o.id = oc.order_id
LEFT JOIN master_attributes ma ON oc.attribute_id = ma.id
GROUP BY o.id
ORDER BY o.created_at DESC;
```

---

## 5. Logika Penambahan Poin Otomatis & Trigger RFM

### A. Implementasi Standar: Django Signals (`signals.py`)
Dalam arsitektur Django, penambahan poin dan pembaruan klaster RFM ditangani secara otomatis melalui *Signals* saat status pesanan beralih ke `'Selesai'`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

@receiver(post_save, sender=Order)
def handle_order_completed(sender, instance, created, **kwargs):
    if instance.status == 'Selesai':
        points_to_add = int(instance.total_price / 10000)
        user = instance.user
        user.total_points += points_to_add
        user.save()
        
        # Panggil kalkulasi ulang RFM K-Means customer tier secara otomatis
        from analytics.services import segment_customers_and_update
        segment_customers_and_update()
```

### B. Alternatif Basis Data: Trigger SQLite
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
