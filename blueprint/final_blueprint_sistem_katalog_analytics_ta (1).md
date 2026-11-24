# Final Blueprint Sistem Katalog Florist & Data Analytics (Tugas Akhir)

Blueprint ini merangkum arsitektur, *tech stack*, struktur data, dan alur sistem final berdasarkan desain *Single Page Application* (SPA). Sistem ini mengadopsi konsep **Dual-Interface** untuk menyeimbangkan kebutuhan bisnis komersial dan penelitian akademis.

---

## 1. Konsep Dual-Interface & Pemisahan Sesi Navigasi

Sistem dirancang agar antarmuka pelanggan dan admin memiliki nuansa, bahasa, dan batasan hak akses sesi yang terpisah secara terpusat:

* **Customer-Facing (Pelanggan):**
  * Dibangun dengan identitas *"Bespoke Botanical Atelier"* menggunakan bahasa retail premium kelas atas tanpa istilah teknis/akademis.
  * Hasil aturan asosiasi FP-Growth dikemas sebagai *"Rekomendasi Spesial Untuk Anda"*, dan segmentasi K-Means dikemas sebagai *"Status Keanggotaan / Tier"*.
  * **Hak Akses Navigasi User:** Dibatasi secara eksklusif hanya untuk:
    1. **Atelier Crafting:** Studio kustomisasi 4 dimensi buket bunga dan banner rekomendasi kombinasi.
    2. **Sreang Club Pass:** Kartu anggota digital, akumulasi poin, target reward, hak istimewa (*perks*), dan riwayat aktivitas pesanan personal pelanggan.
* **Admin-Facing (Pengelola & Peneliti TA):**
  * Berfungsi sebagai pusat kendali operasional sekaligus *Data Mining Gateway*.
  * **Hak Akses Navigasi Admin (Hak Akses Penuh):** Admin dapat mengakses antarmuka pelanggan sekaligus panel manajemen pengelola:
    1. **Atelier Crafting & Sreang Club Pass:** Meninjau dan mensimulasikan antarmuka pelanggan.
    2. **Riwayat Pesanan:** Memantau antrean pesanan masuk, mengubah status pemesanan, dan **mengekspor seluruh data riwayat transaksi ke format CSV** (`/api/export/orders`).
    3. **Stok & Inventori:** Mengelola ketersediaan fisik komponen dan penyesuaian harga *price modifier*.
    4. **Live Analytical Hub:** Memantau evaluasi metrik algoritma secara langsung (Silhouette Score, Support, Confidence, Lift Ratio) dan menyediakan tombol ekspor dataset CSV untuk diolah di **Google Colab**.

---

## 2. Arsitektur Sistem & Tech Stack

Sistem dibangun menggunakan arsitektur **Decoupled Client-Server (REST API)** yang modern, modular, dan handal untuk kebutuhan komputasi data penelitian:

* **Front-End:** **React.js** (Single Page Application dengan Vite).
  * Menggunakan pendekatan berbasis komponen (*component-driven architecture*), modular state hooks (`useState`, `useEffect`), dan API service terpusat (Axios / Fetch).
  * Desain antarmuka ditata dengan **Tailwind CSS** mengacu pada *design tokens Botanical Atelier* (*Cypress Forest* `#143823`, *Golden Amber* `#E5A93C`, *Crimson Dahlia* `#B91C1C`, dan *Warm Parchment* `#FCF9F4`) dengan tipografi *Playfair Display* dan *Plus Jakarta Sans*.
* **Back-End:** **Python** dengan framework **Django** dan **Django REST Framework (DRF)**.
  * Menangani REST API untuk otentikasi cepat, transaksi pesanan, manajemen inventori, dan sistem *loyalty*.
  * Menggunakan **fungsi Python Native** (struktur *tree/dictionary* & kalkulasi jarak *Euclidean* murni tanpa membebani server dengan *library* berat) yang terintegrasi di *service layer* Django untuk menghitung rekomendasi aturan asosiasi **FP-Growth** secara *real-time* di katalog serta memperbarui label klaster **K-Means (RFM)** pelanggan.
  * Menggunakan *Django Signals* (`post_save`) pada model transaksi pesanan untuk secara otomatis memicu penambahan poin loyalitas dan perhitungan ulang posisi klaster RFM saat pesanan diselesaikan.
* **Database:** **SQLite lokal** (`db.sqlite3`).
  * Praktis, portabel, dan mandiri untuk demo lokal/sidang TA tanpa ketergantungan server database eksternal.
  * Terkelola secara deklaratif menggunakan **Django ORM** dengan integritas relasi ketat (*Foreign Key constraints* & *Indexes*), serta kompatibel untuk migrasi ke **PostgreSQL / MySQL** kapan saja.
* **Sistem Otentikasi (Login):**
  * **Pelanggan:** Masuk cepat menggunakan kombinasi **Username** dan **Nomor Telepon** (disimpan unik di tabel pengguna, tanpa password rumit) yang langsung menghubungkan transaksi dan poin *loyalty*.
  * **Admin:** Masuk melalui portal pengelola dengan kredensial PIN / Password keamanan khusus.
* **Data Mining Lab (Penelitian TA):** **Google Colab** digunakan sebagai lingkungan analisis eksternal untuk mengolah, memvalidasi, dan memvisualisasikan dataset `.csv` yang diekspor dari Django (menggunakan `pandas`, `matplotlib`/`seaborn`, `scikit-learn`, dan `mlxtend` untuk *Elbow Method*, *Silhouette Score*, dan *association rules network*).

---

## 3. Struktur Database Inti (Django ORM & SQLite)

Struktur model basis data dioptimalkan untuk menjaga integritas relasional dan mengakomodasi 4 dimensi kustomisasi buket:

### A. Tabel `users` (Basis Data Pelanggan & Segmentasi RFM)
Didefinisikan melalui Custom User Model di Django:
* `id` (BigAutoField PK)
* `username` (CharField UNIQUE - Identitas Pengguna Utama)
* `phone_number` (CharField UNIQUE - Nomor WhatsApp / Identitas Pelanggan untuk RFM)
* `name` (CharField - Nama Lengkap Pelanggan)
* `role` (CharField: `'customer'`, `'admin'`)
* `pin_code` (CharField NULL - Khusus Otentikasi Admin)
* `total_points` (IntegerField DEFAULT 0 - Akumulasi Poin Loyalitas)
* `tier_status` (CharField DEFAULT `'Bronze Tier'` - Label hasil klastering K-Means: *Gold*, *Silver*, *Bronze*)
* `created_at` (DateTimeField auto_now_add=True)
* `updated_at` (DateTimeField auto_now=True)

### B. Tabel `master_attributes` (Komponen Katalog 4 Dimensi)
* `id` (BigAutoField PK)
* `category` (CharField: `'bunga_utama'`, `'bahan_wrap'`, `'gaya_rangkaian'`, `'ukuran'`)
* `name` (CharField - Contoh: `'Mawar Merah Holland'`, `'Cellophane Matte Transparan'`)
* `price_modifier` (DecimalField / FloatField DEFAULT 0.0 - Biaya tambahan komponen)
* `stock` (IntegerField DEFAULT 0 - Kuantitas stok fisik)
* `is_active` (BooleanField DEFAULT True - Status visibilitas katalog)
* `created_at` (DateTimeField auto_now_add=True)

### C. Tabel `orders` (Transaksi & Penjadwalan Pre-Order)
* `id` (CharField PK - Format: `'#SRG-XXXX'`)
* `user` (ForeignKey -> `users.id`, on_delete=models.RESTRICT)
* `pickup_date` (DateField - Format YYYY-MM-DD)
* `pickup_time_slot` (CharField: `'09:00 - 10:00 WIB'`, `'11:00 - 12:00 WIB'`, `'16:00 - 17:00 WIB'`)
* `card_theme` (CharField NULL - Contoh: *Birthday*, *Anniversary*, *Graduation*)
* `card_message` (TextField NULL - Pesan ucapan personal)
* `base_price` (DecimalField DEFAULT 185000.0)
* `points_used` (IntegerField DEFAULT 0)
* `points_earned` (IntegerField DEFAULT 0)
* `total_price` (DecimalField - Nilai transaksi akhir)
* `status` (CharField: `'Menunggu'`, `'Diproses'`, `'Selesai'`, `'Dibatalkan'`)
* `created_at` (DateTimeField auto_now_add=True)

### D. Tabel `order_customizations` (Dataset Asosiasi / FP-Growth)
Menyimpan detail kombinasi 4 komponen per pesanan untuk diekstrak menjadi *Itemsets*:
* `id` (BigAutoField PK)
* `order` (ForeignKey -> `orders.id`, on_delete=models.CASCADE)
* `attribute` (ForeignKey -> `master_attributes.id`, on_delete=models.RESTRICT)

---

## 4. Alur Pemrosesan Data & Ekstraksi Analitik (Django & Google Colab)

1. **In-App Analytics (Python Native di Django Backend):**
   * **Rekomendasi Katalog FP-Growth:** Saat pelanggan membuka halaman katalog React.js, endpoint `GET /api/catalog/recommendations` memanggil fungsi Python native FP-Growth pada riwayat transaksi berstatus `'Selesai'`. Sistem mengekstrak pola kombinasi 4 item dengan nilai *Confidence* dan *Lift* tertinggi, lalu mengirimkannya sebagai data banner *"Rekomendasi Spesial Untuk Anda"*.
   * **Segmentasi Pelanggan RFM K-Means:** Saat admin memperbarui status pesanan menjadi `'Selesai'`, sinyal *Django Signals* atau service handler secara otomatis menambahkan poin loyalitas ke akun pengguna (Rp 10.000 = 1 poin) dan mengeksekusi fungsi Python native K-Means untuk memperbarui label `tier_status` pelanggan (*Gold*, *Silver*, *Bronze*).
2. **External Data Mining Lab (Google Colab):**
   * Admin dapat mengunduh tiga dataset transaksional bersih melalui modul admin:
     * **`kmeans_rfm.csv` (`/api/export/kmeans`):** Kolom `Customer_ID`, `Nama_Pelanggan`, `Recency_Days`, `Frequency_Count`, `Monetary_Value`.
     * **`fp_growth.csv` (`/api/export/fpgrowth`):** Kolom `Transaction_ID`, `Itemsets`.
     * **`riwayat_pesanan.csv` (`/api/export/orders`):** Seluruh data riwayat transaksi detail operasional.
   * Dataset diunggah ke **Google Colab** untuk pengujian mendalam (*Elbow Method*, *Silhouette Score*, *Davies-Bouldin Index*, serta visualisasi *scatter plot* klaster dan *association rules network*) sebagai bukti empiris pada bab hasil dan pembahasan Tugas Akhir.
