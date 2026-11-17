# Final Blueprint Sistem Katalog Florist & Data Analytics (Tugas Akhir)

Blueprint ini merangkum arsitektur, struktur data, dan alur sistem final berdasarkan desain *Single Page Application* (SPA). Sistem ini mengadopsi konsep **Dual-Interface** untuk menyeimbangkan kebutuhan bisnis komersial dan penelitian akademis.

## 1. Konsep Dual-Interface (Pemisahan Lingkungan)

Sistem dirancang agar antarmuka pelanggan dan admin memiliki nuansa dan bahasa yang sama sekali berbeda:
*   **Customer-Facing (Pelanggan):** Dibangun dengan identitas "Bespoke Botanical Atelier". Menggunakan bahasa retail premium kelas atas. Tidak ada istilah teknis, algoritma, atau Tugas Akhir. Fitur rekomendasi dari FP-Growth dikemas sebagai *"Rekomendasi Spesial Untuk Anda"*, dan segmentasi K-Means dikemas sebagai *"Status Keanggotaan / Tier"*.
*   **Admin-Facing (Pengelola/Peneliti):** Berfungsi sebagai pusat kendali operasional sekaligus *Data Mining Gateway*. Menampilkan evaluasi algoritma secara langsung (Support, Confidence, Lift, Silhouette Score) dan menyediakan modul ekspor data siap pakai untuk Jupyter Notebook/Python.

## 2. Arsitektur Sistem (High-Level Architecture)

*   **Front-End:** Single Page Application (SPA) menggunakan HTML5, Tailwind CSS (dengan custom design tokens dari `DESIGN.md`), dan Vanilla JavaScript untuk navigasi DOM dinamis tanpa *reload*.
*   **Back-End (Server-Side):** API yang menangani otentikasi (berbasis No. HP), perhitungan *pricing* dinamis kustomisasi, manajemen status pesanan, dan injeksi *loyalty points*.
*   **Database:** Relational Database (RDBMS) yang dirancang ketat dengan *Foreign Keys* untuk mencegah anomali data (krusial untuk keakuratan algoritma TA).

## 3. Struktur Database Inti

Struktur tabel dioptimalkan untuk mengakomodasi 4 dimensi kustomisasi buket.

**A. Tabel `users` (Basis Data Segmentasi/RFM)**
*   `id` (PK)
*   `role` (ENUM: 'customer', 'admin')
*   `phone_number` (Unique - Identitas Login)
*   `name`
*   `total_points`
*   `tier_status` (Label hasil klastering, misal: Gold, Silver)
*   *Atribut RFM (Kalkulasi dari tabel orders):* Recency, Frequency, Monetary.

**B. Tabel `master_attributes` (Komponen Katalog)**
*   `id` (PK)
*   `category` (ENUM: 'bunga_utama', 'bahan_wrap', 'gaya_rangkaian', 'ukuran')
*   `name` (Contoh: Mawar Merah Holland, Cellophane Matte)
*   `price_modifier` (Harga tambahan)
*   `stock` (Jumlah fisik)
*   `is_active` (Boolean)

**C. Tabel `orders` (Transaksi & Penjadwalan)**
*   `id` (PK, Format: #SRG-XXXX)
*   `user_id` (FK)
*   `pickup_date` (Tanggal Ambil)
*   `pickup_time_slot` (ENUM: Pagi, Siang, Sore)
*   `base_price` & `total_price`
*   `status` (ENUM: 'Menunggu', 'Diproses', 'Selesai')
*   `created_at`

**D. Tabel `order_customizations` (Dataset Asosiasi / FP-Growth)**
Menyimpan detail kombinasi setiap pesanan untuk diekstrak menjadi *Itemsets*.
*   `id` (PK)
*   `order_id` (FK)
*   `attribute_id` (FK -> master_attributes.id)

## 4. Pemetaan Data & Ekspor Modul TA

Dashboard Admin memiliki tombol ekspor yang secara otomatis melakukan *query* ke database dan men-generate file dalam format berikut:

### A. Modul Ekspor FP-Growth
*   **Target:** `fp_growth_matrix.csv`
*   **Proses Data:** Melakukan *Group By* pada `order_customizations` berdasarkan `order_id`.
*   **Output:** Baris transaksional murni yang berisi *Itemsets* (Contoh: `Mawar Merah, Cellophane Matte, Korean Style, Standard`).

### B. Modul Ekspor K-Means (RFM)
*   **Target:** `kmeans_rfm.csv`
*   **Proses Data:** Menghitung selisih hari pesanan terakhir (Recency), menghitung jumlah baris pesanan per `user_id` (Frequency), dan melakukan *Sum* pada `total_price` per `user_id` (Monetary).
*   **Output:** Tabel dengan kolom `Phone_Number`, `Recency`, `Frequency`, `Monetary`.

## 5. Alur Pengguna Akhir (User Flow)

**Jalur Pelanggan (Customer Journey):**
1.  **Login Cepat:** Masuk menggunakan Nomor HP dan Nama (tanpa password rumit).
2.  **Kustomisasi Produk:** Masuk ke "Atelier Crafting Studio". Pelanggan wajib memilih 4 atribut (Bunga, Wrap, Gaya, Ukuran).
3.  *(Background Process)* Sistem mengecek aturan FP-Growth. Jika kombinasi pelanggan cocok dengan pola populer, UI akan menampilkan "Rekomendasi Spesial Untuk Anda".
4.  **Checkout & Pre-Order:** Menentukan tanggal dan slot jam *pickup* agar tidak antre, lalu mengkonfirmasi pesanan.
5.  **Cek Sreang Club:** Melihat akumulasi poin, target hadiah (Voucher/Buket Gratis), dan tingkat keanggotaan (berdasarkan segmentasi K-Means yang tersembunyi).

**Jalur Admin (Pengelola & Peneliti TA):**
1.  **Akses Terbatas:** Login menggunakan Email dan PIN melalui portal tersembunyi.
2.  **Manajemen Operasional:** Menerima pesanan masuk, menyiapkan buket, dan mengubah status menjadi "Selesai". *(Trigger: Saat status "Selesai", sistem otomatis menambahkan poin ke dompet pelanggan bersangkutan).*
3.  **Pemantauan Inventori:** Mengedit harga komponen atau menandai stok bunga yang habis (langsung memperbarui katalog pelanggan).
4.  **Ekstraksi Data TA:** Melihat metrik algoritma langsung di layar (Lift, Support, Silhouette Score) dan menekan tombol Unduh CSV untuk diolah di Jupyter Notebook pada saat bimbingan/sidang TA.