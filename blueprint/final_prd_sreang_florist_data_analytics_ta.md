# Product Requirements Document (PRD) - Final

**Nama Proyek:** Sreang Florist — Bespoke Botanical Atelier & Retail Analytics System
**Fokus Utama:** Operasional E-Commerce Florist & Pengumpulan Dataset Tugas Akhir (K-Means & FP-Growth)
**Tech Stack:** HTML5/Tailwind/Vanilla JS (SPA), Python FastAPI (Native Algorithms), SQLite/MySQL, Google Colab
**Status:** Final (Selaras dengan Blueprint & Prototipe UI)

## 1. Ringkasan Proyek (Overview)

**Sreang Florist** adalah sistem aplikasi berbasis web yang dirancang dengan pendekatan *Dual-Interface* untuk melayani dua kebutuhan utama secara simultan:

1. **Sisi Bisnis (Customer-Facing):** Menyediakan pengalaman berbelanja bunga yang elegan, cepat, dan personal (*Bespoke Botanical Atelier*) menggunakan antarmuka SPA yang responsif tanpa mengekspos istilah teknis atau akademis kepada pelanggan.
2. **Sisi Penelitian (Admin-Facing):** Bertindak sebagai instrumen pengumpulan data terstruktur (*Data Mining Gateway*) berbasis FastAPI & SQLite yang mencatat identitas pelanggan dan kombinasi atribut produk secara presisi untuk diolah di **Google Colab** menggunakan algoritma **K-Means Clustering** (segmentasi RFM) dan **FP-Growth** (aturan asosiasi produk).

## 2. Tujuan & Metrik Keberhasilan (Objectives & Success Metrics)

### Tujuan Utama
* **Operasional:** Mempercepat proses pemesanan buket kustom, mengurangi antrean fisik melalui penjadwalan *pickup* (Pre-Order), dan meningkatkan retensi pelanggan melalui sistem loyalitas (*Sreang Club*).
* **Akademis (TA):** Menghasilkan dataset transaksional yang bersih (*clean data*), bebas dari *orphan records* berkat relasi *Foreign Key* yang ketat, serta menyediakan fungsi algoritma Python *native* di *backend* dan ekspor CSV yang siap dianalisis di **Google Colab**.

### Metrik Keberhasilan (KPI)
* **Kecepatan Akses:** Pelanggan dapat masuk (Login/Register) dan menyelesaikan kustomisasi produk dalam waktu **< 2 menit** tanpa jeda *reload* halaman (SPA).
* **Integritas Data:** 100% transaksi yang berstatus "Selesai" tercatat lengkap dengan 4 atribut kustomisasi (untuk FP-Growth) dan terhubung ke Nomor HP unik (untuk K-Means).
* **Kesiapan Ekspor & Lab:** Modul Admin mampu men-generate file `kmeans_rfm.csv` dan `fp_growth.csv` melalui *endpoint* FastAPI yang langsung terbaca tanpa error di notebook **Google Colab**.

## 3. Target Pengguna & Konsep Dual-Interface

### A. Pelanggan (Customer)
* **Karakteristik:** Pembeli buket bunga yang mengakses web melalui *smartphone* dan menginginkan proses pemesanan praktis tanpa *password*.
* **Pengalaman UI:** Menggunakan bahasa retail kelas atas. Hasil kalkulasi *native* FP-Growth dari FastAPI ditampilkan sebagai **"Rekomendasi Spesial Untuk Anda"**, sedangkan hasil klaster K-Means ditampilkan sebagai **"Status Keanggotaan / Tier"** (misal: *Gold Tier*).

### B. Admin / Peneliti (Mahasiswa S1 Teknik Informatika)
* **Karakteristik:** Pengelola operasional florist sekaligus peneliti TA yang membutuhkan kontrol penuh atas pesanan masuk, stok atribut, dan ekstraksi data.
* **Pengalaman UI:** Antarmuka analitis (*Live Analytical Hub*) yang menampilkan metrik evaluasi algoritma secara transparan serta tombol ekspor dataset CSV untuk kebutuhan pengujian di **Google Colab**.

## 4. Spesifikasi Kebutuhan Fungsional (Functional Requirements)

### 4.1 Modul Otentikasi Cepat (Berbasis Nomor HP)
* **User Story:** *Sebagai pelanggan, saya ingin mendaftar atau masuk hanya dengan Nama dan Nomor WhatsApp/HP agar transaksi saya tercatat dan poin loyalty saya terakumulasi secara otomatis.*
* **Acceptance Criteria:**
  * Form pelanggan hanya memiliki 2 input: **Nama Lengkap** dan **Nomor HP** (disimpan unik di tabel `users` SQLite).
  * Front-End mengirim request `POST /api/auth/login` ke FastAPI; jika nomor belum ada, sistem otomatis membuat akun baru.
  * Tersedia tab terpisah (**Portal Admin**) dengan otentikasi Email & PIN khusus untuk pengelola.

### 4.2 Modul Katalog & Studio Kustomisasi (4 Dimensi Atribut)
* **User Story:** *Sebagai pelanggan, saya ingin merangkai buket sesuai selera saya dengan memilih bunga, pembungkus, gaya, dan ukurannya, serta melihat rekomendasi kombinasi terbaik.*
* **Acceptance Criteria:**
  * Pelanggan **wajib** memilih 4 atribut kustomisasi sebelum memasukkan produk ke keranjang:
    1. **Jenis Bunga Utama** (Mawar Merah Holland, Krisan Kuning, Baby's Breath).
    2. **Jenis Bahan Wrap** (Cellophane Matte, Spunbond Tebal).
    3. **Gaya Rangkaian** (Korean Style, Classic Round).
    4. **Ukuran / Kuantitas Tangkai** (Standard 10 Tangkai, Deluxe 18 Tangkai, Grandeur 25 Tangkai).
  * Harga total dihitung secara *real-time* di sisi klien (Vanilla JS) dan divalidasi ulang oleh FastAPI saat *checkout*.
  * Sistem mengambil *endpoint* `GET /api/recommendations` yang ditenagai fungsi **Python Native FP-Growth** di FastAPI untuk menampilkan *banner* **"Rekomendasi Spesial Untuk Anda"**.

### 4.3 Modul Keranjang & Penjadwalan Pre-Order
* **User Story:** *Sebagai pelanggan, saya ingin menentukan tanggal dan slot jam pengambilan bunga agar bunga dirangkai dalam kondisi segar dan tidak terjadi antrean.*
* **Acceptance Criteria:**
  * Menampilkan ringkasan item beserta detail 4 atribut yang dipilih.
  * Menyediakan input pemilihan **Tanggal Pickup** dan **Slot Jam Pengambilan** (Pagi, Siang, Sore).
  * Menyediakan kolom pesan kartu ucapan (*custom note*) dan mengirim seluruh payload transaksi melalui `POST /api/orders`.

### 4.4 Modul Sistem Loyalty (*Sreang Club*)
* **User Story:** *Sebagai pelanggan, saya ingin melihat jumlah poin saya dan menukarkannya dengan voucher atau hadiah bunga gratis.*
* **Acceptance Criteria:**
  * Menampilkan kartu anggota digital (*Sreang Club Pass*) beserta status tier keanggotaan hasil klastering **Python Native K-Means**.
  * Menampilkan saldo poin aktif dan *progress bar* visual menuju target hadiah utama.
  * Poin bertambah secara otomatis di database SQLite **hanya ketika** Admin mengubah status pesanan menjadi **"Selesai"**.

### 4.5 Dashboard Admin & Modul Ekspor Data TA
* **User Story:** *Sebagai admin dan peneliti TA, saya ingin memantau pesanan masuk, mengelola stok atribut, dan mengekspor dataset CSV untuk diolah dan divisualisasikan di Google Colab.*
* **Acceptance Criteria:**
  * **Manajemen Pesanan:** Mengubah status pesanan (`Menunggu` $\rightarrow$ `Diproses` $\rightarrow$ `Selesai`) via `PATCH /api/orders/{id}/status`. Perubahan ke `Selesai` memicu kalkulasi poin otomatis dan pembaruan segmen RFM.
  * **Manajemen Inventori:** Memperbarui harga satuan dan ketersediaan stok atribut di database.
  * **Modul Ekspor Dataset (FastAPI StreamingResponse CSV):**
    * **Ekspor K-Means (`GET /api/export/kmeans`):** Mengunduh file `kmeans_rfm.csv` berisi kolom `Customer_ID`, `Nama_Pelanggan`, `Recency_Days`, `Frequency_Count`, dan `Monetary_Value`.
    * **Ekspor FP-Growth (`GET /api/export/fpgrowth`):** Mengunduh file `fp_growth.csv` berisi `Transaction_ID` dan `Itemsets` (kombinasi atribut per transaksi yang dipisahkan koma) untuk diimpor langsung ke **Google Colab**.

## 5. Kebutuhan Non-Fungsional & Standar Desain

* **Portabilitas & Kecepatan Demo:** Penggunaan **SQLite** dan **FastAPI** memastikan seluruh aplikasi berjalan secara lokal dengan satu perintah (`uvicorn main:app`) tanpa ketergantungan pada server database eksternal saat sidang TA.
* **Design System (*Botanical Atelier*):** Menggunakan palet warna *Cypress Forest* (`#143823`), *Golden Amber* (`#E5A93C`), *Crimson Dahlia* (`#B91C1C`), dan *Warm Parchment* (`#FCF9F4`) dengan kombinasi tipografi *Playfair Display* dan *Plus Jakarta Sans*.
* **Integritas Relasional:** Wajib mengaktifkan `PRAGMA foreign_keys = ON;` pada setiap koneksi SQLite di FastAPI untuk menjaga konsistensi relasi antar tabel.