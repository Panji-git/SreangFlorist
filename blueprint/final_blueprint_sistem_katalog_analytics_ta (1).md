# Final Blueprint Sistem Katalog Florist & Data Analytics (Tugas Akhir)

Blueprint ini merangkum arsitektur, *tech stack*, struktur data, dan alur sistem final berdasarkan desain *Single Page Application* (SPA). Sistem ini mengadopsi konsep **Dual-Interface** untuk menyeimbangkan kebutuhan bisnis komersial dan penelitian akademis.

## 1. Konsep Dual-Interface (Pemisahan Lingkungan)

Sistem dirancang agar antarmuka pelanggan dan admin memiliki nuansa dan bahasa yang sama sekali berbeda:

* **Customer-Facing (Pelanggan):** Dibangun dengan identitas "Bespoke Botanical Atelier". Menggunakan bahasa retail premium kelas atas tanpa istilah teknis/akademis. Hasil aturan asosiasi FP-Growth dikemas sebagai *"Rekomendasi Spesial Untuk Anda"*, dan segmentasi K-Means dikemas sebagai *"Status Keanggotaan / Tier"*.
* **Admin-Facing (Pengelola/Peneliti):** Berfungsi sebagai pusat kendali operasional sekaligus *Data Mining Gateway*. Menampilkan evaluasi algoritma secara langsung dan menyediakan modul ekspor dataset CSV untuk diolah lebih lanjut di **Google Colab**.

## 2. Arsitektur Sistem & Tech Stack

Sistem dibangun menggunakan arsitektur **Decoupled Client-Server (REST API)** yang ringan namun sangat presisi untuk kebutuhan komputasi data:

* **Front-End:** Single Page Application (SPA) menggunakan **HTML5**, **Tailwind CSS** (dengan custom design tokens *Botanical Atelier*), dan **Vanilla JavaScript** (`fetch` API) untuk komunikasi asinkron tanpa *reload* halaman.
* **Back-End:** **Python** dengan framework **FastAPI**. 
  * Menangani REST API untuk otentikasi, transaksi, manajemen stok, dan sistem *loyalty*.
  * Menggunakan **fungsi Python Native** (struktur *tree/dictionary* & kalkulasi jarak *Euclidean* murni tanpa membebani server dengan *library* berat) untuk menghitung rekomendasi aturan asosiasi **FP-Growth** secara *real-time* di katalog serta memperbarui label klaster **K-Means (RFM)** pelanggan.
* **Database:** **SQLite** (praktis dan portabel untuk demo lokal/sidang tanpa perlu instalasi server terpisah) yang dirancang dengan relasi *Foreign Keys* ketat (`PRAGMA foreign_keys = ON;`), serta kompatibel untuk migrasi ke **MySQL**.
* **Data Mining Lab (Penelitian TA):** **Google Colab** digunakan sebagai lingkungan analisis eksternal untuk mengolah, memvalidasi, dan memvisualisasikan dataset `.csv` yang diekspor dari modul Admin (menggunakan `pandas`, `matplotlib`/`seaborn`, serta perbandingan evaluasi algoritma).

## 3. Struktur Database Inti (SQLite / MySQL)

Struktur tabel dioptimalkan untuk mengakomodasi 4 dimensi kustomisasi buket:

**A. Tabel `users` (Basis Data Segmentasi/RFM)**
* `id` (INTEGER PK AUTOINCREMENT)
* `role` (TEXT: 'customer', 'admin')
* `phone_number` (TEXT UNIQUE - Identitas Login Utama)
* `name` (TEXT)
* `pin_code` (TEXT NULL - Khusus Admin)
* `total_points` (INTEGER)
* `tier_status` (TEXT - Label hasil klastering K-Means, misal: 'Gold Tier', 'Silver Tier')

**B. Tabel `master_attributes` (Komponen Katalog)**
* `id` (INTEGER PK AUTOINCREMENT)
* `category` (TEXT: 'bunga_utama', 'bahan_wrap', 'gaya_rangkaian', 'ukuran')
* `name` (TEXT - Contoh: 'Mawar Merah Holland', 'Cellophane Matte')
* `price_modifier` (REAL)
* `stock` (INTEGER)
* `is_active` (INTEGER / Boolean: 1 atau 0)

**C. Tabel `orders` (Transaksi & Penjadwalan)**
* `id` (TEXT PK - Format: '#SRG-XXXX')
* `user_id` (INTEGER FK -> `users.id`)
* `pickup_date` (TEXT - Format YYYY-MM-DD)
* `pickup_time_slot` (TEXT)
* `card_theme` & `card_message` (TEXT)
* `base_price`, `points_used`, `points_earned`, `total_price` (REAL / INTEGER)
* `status` (TEXT: 'Menunggu', 'Diproses', 'Selesai', 'Dibatalkan')
* `created_at` (DATETIME)

**D. Tabel `order_customizations` (Dataset Asosiasi / FP-Growth)**
Menyimpan detail kombinasi setiap pesanan untuk diekstrak menjadi *Itemsets*.
* `id` (INTEGER PK AUTOINCREMENT)
* `order_id` (TEXT FK -> `orders.id`)
* `attribute_id` (INTEGER FK -> `master_attributes.id`)

## 4. Alur Pemrosesan Data (FastAPI Native & Google Colab)

1. **In-App Analytics (Python Native di FastAPI):**
   * Saat pelanggan membuka halaman Katalog, FastAPI menjalankan fungsi Python *native* FP-Growth ringan pada histori transaksi `Selesai` untuk mencari *rule* dengan nilai *Confidence* dan *Lift* tertinggi, lalu mengirimkannya via JSON ke Front-End sebagai *"Rekomendasi Spesial"*.
   * Saat pesanan selesai, fungsi Python *native* K-Means menghitung ulang posisi *centroid* RFM pelanggan untuk memperbarui `tier_status` mereka secara otomatis.
2. **External Data Mining Lab (Google Colab):**
   * Admin menekan tombol unduh CSV pada *Dashboard Admin* (`kmeans_rfm.csv` dan `fp_growth.csv`).
   * File CSV diunggah ke **Google Colab** untuk dilakukan pengujian parameter mendalam (*Elbow Method*, *Silhouette Score*, *Davies-Bouldin Index*, serta visualisasi *scatter plot* klaster dan *association rules network*) sebagai bukti empiris bab hasil dan pembahasan Tugas Akhir.