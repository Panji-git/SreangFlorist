# Sreang Florist — Bespoke Botanical Atelier & Retail Analytics System

Aplikasi E-Commerce Katalog Florist & Sistem Analitik Ritel berbasis Web dengan pendekatan **Dual-Interface** untuk kebutuhan operasional toko bunga komersial sekaligus penelitian Tugas Akhir (*Data Mining* menggunakan algoritma **K-Means Clustering** untuk segmentasi pelanggan RFM dan **FP-Growth** untuk aturan asosiasi produk).

---

## 🌸 Konsep Dual-Interface

1. **Customer-Facing (Pelanggan):**
   - Identitas *"Bespoke Botanical Atelier"* dengan nuansa retail premium.
   - Tanpa istilah teknis/akademis.
   - Hasil kalkulasi FP-Growth disajikan sebagai **"Rekomendasi Spesial Untuk Anda"**.
   - Hasil segmentasi K-Means disajikan sebagai **"Status Keanggotaan / Tier"** (Gold, Silver, Bronze) di *Sreang Club*.

2. **Admin-Facing (Pengelola & Peneliti TA):**
   - Pusat kendali operasional pemesanan, ketersediaan stok komponen bunga, dan status *pre-order*.
   - *Data Mining Gateway* yang menampilkan metrik algoritma langsung (Support, Confidence, Lift, Silhouette Score).
   - Ekspor dataset transaksional siap pakai (`kmeans_rfm.csv` dan `fp_growth.csv`) untuk diolah di **Google Colab**.

---

## 🛠️ Arsitektur & Tech Stack

- **Front-End:** Single Page Application (SPA) murni dengan HTML5, Tailwind CSS (*Design Tokens Botanical Atelier*), dan Vanilla JavaScript (`fetch` API).
- **Back-End:** Python **FastAPI** dengan algoritma *Python Native* (struktur pohon/dictionary & perhitungan jarak *Euclidean* murni tanpa membebani server).
- **Database:** **SQLite** (`sreang_florist.db`) dengan integritas relasional ketat (`PRAGMA foreign_keys = ON;`) dan *triggers*.
- **Data Mining Lab:** **Google Colab** untuk validasi mendalam (Elbow Method, Silhouette Analysis, visualisasi *scatter plot* klaster, dan graf jaringan aturan asosiasi).

---

## 📂 Struktur Direktori Proyek

```text
SreangFlorist_Ecatalog/
├── .gitignore               # Pengecualian venv/, __pycache__/, *.pyc, .env, *.db
├── README.md                # Dokumentasi arsitektur dan panduan proyek
├── requirements.txt         # Dependensi Python (FastAPI, Uvicorn, Pydantic)
├── blueprint/               # Dokumen spesifikasi, PRD, dan skema database TA
│   ├── final_blueprint_sistem_katalog_analytics_ta (1).md
│   ├── final_blueprint_sistem_katalog_analytics_ta.md
│   ├── final_prd_sreang_florist_data_analytics_ta.md
│   └── skema_database_query_analitik_ta.md
├── backend/
│   ├── __init__.py
│   ├── database.py          # Koneksi SQLite, foreign key enforcement, session generator
│   ├── schema.sql           # DDL SQLite, indeks performa, dan trigger penambahan poin
│   ├── seeder.py            # Auto-seeder master data & 40 transaksi dummy realistis
│   ├── main.py              # Inisialisasi FastAPI & static files mounting
│   ├── analytics/           # Modul in-app analytics (RFM K-Means & FP-Growth)
│   └── routers/             # Endpoint REST API (auth, catalog, orders, loyalty, export)
├── frontend/
│   ├── index.html           # Single Page Application entry
│   ├── css/
│   │   └── style.css        # Custom styling & token warna Botanical Atelier
│   ├── js/
│   │   └── app.js           # Client-side SPA routing & state controller
│   └── assets/              # Logo dan media visual toko
├── colab/                   # Script pendukung & notebook Google Colab TA
└── data/                    # Penyimpanan data lokal
```

---

## 🗄️ Skema Database (`sreang_florist.db`)

1. **`users`**: Basis data pelanggan (identitas nomor WhatsApp/HP) dan akun admin.
2. **`master_attributes`**: Komponen 4 dimensi buket (*bunga utama*, *bahan wrap*, *gaya rangkaian*, *ukuran*).
3. **`orders`**: Transaksi pemesanan, jadwal pickup, total harga, status, dan akumulasi poin.
4. **`order_customizations`**: Pivot itemset 4 atribut kustomisasi per pesanan untuk input FP-Growth.
5. **Trigger `after_order_completed`**: Menambahkan poin otomatis ke dompet pelanggan (kelipatan Rp 10.000 = 1 poin) saat status pesanan beralih ke `Selesai`.

---

## 🚀 Panduan Memulai (Quickstart)

### 1. Persiapan Virtual Environment & Dependensi
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Inisialisasi Database & Seeder 40 Transaksi Dummy
Jalankan script seeder untuk membuat file database `sreang_florist.db` beserta 10 master atribut, akun admin, 13 profil pelanggan, dan 40 transaksi yang memiliki pola asosiasi dan distribusi RFM realistis:
```bash
python3 backend/seeder.py
```

### 3. Menjalankan Server Backend FastAPI
```bash
uvicorn backend.main:app --reload
```
Aplikasi dapat diakses melalui:
- **Web SPA:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
