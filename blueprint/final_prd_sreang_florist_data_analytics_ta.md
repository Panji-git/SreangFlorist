# Product Requirements Document (PRD) - Final

**Nama Proyek:** Sreang Florist — Bespoke Botanical Atelier & Retail Analytics System  
**Fokus Utama:** Operasional E-Commerce Florist & Pengumpulan Dataset Tugas Akhir (K-Means & FP-Growth)  
**Tech Stack:** React.js (Vite + Tailwind CSS), Python Django & Django REST Framework (Native Algorithms), SQLite lokal, Google Colab  
**Status:** Final (Selaras dengan Blueprint & Arsitektur Dual-Interface Terpusat)  

---

## 1. Ringkasan Proyek (Overview)

**Sreang Florist** adalah sistem aplikasi berbasis web yang dirancang dengan pendekatan **Dual-Interface** terpusat untuk melayani dua kebutuhan utama secara simultan:

1. **Sisi Bisnis (Customer-Facing):** Menyediakan pengalaman berbelanja bunga yang elegan, cepat, dan personal (*Bespoke Botanical Atelier*) menggunakan antarmuka Single Page Application (SPA) berbasis **React.js** tanpa mengekspos istilah teknis atau akademis kepada pelanggan.
2. **Sisi Penelitian (Admin-Facing):** Bertindak sebagai instrumen pengumpulan data terstruktur (*Data Mining Gateway*) berbasis **Django & Django REST Framework (DRF)** dengan basis data **SQLite lokal** yang mencatat identitas pelanggan (`username` dan `phone_number`) serta kombinasi 4 dimensi atribut produk secara presisi untuk diolah di **Google Colab** menggunakan algoritma **K-Means Clustering** (segmentasi RFM) dan **FP-Growth** (aturan asosiasi produk).

---

## 2. Tujuan & Metrik Keberhasilan (Objectives & Success Metrics)

### Tujuan Utama
* **Operasional:** Mempercepat proses pemesanan buket kustom, mengurangi antrean fisik melalui penjadwalan *pickup* (Pre-Order), dan meningkatkan retensi pelanggan melalui sistem loyalitas (*Sreang Club*).
* **Akademis (TA):** Menghasilkan dataset transaksional yang bersih (*clean data*), bebas dari *orphan records* berkat relasi *Foreign Key* ketat pada Django ORM, serta menyediakan fungsi algoritma Python *native* di *service layer* backend dan ekspor 3 jenis file CSV yang siap dianalisis di **Google Colab** maupun untuk pelaporan bisnis.

### Metrik Keberhasilan (KPI)
* **Kecepatan Akses:** Pelanggan dapat masuk (Login/Register menggunakan Username & No. Telepon) dan menyelesaikan kustomisasi produk dalam waktu **< 2 menit** tanpa jeda *reload* halaman (React SPA).
* **Integritas Data:** 100% transaksi yang berstatus "Selesai" tercatat lengkap dengan 4 atribut kustomisasi (untuk FP-Growth) dan terhubung ke Username serta Nomor WhatsApp/HP unik (untuk K-Means).
* **Kesiapan Ekspor & Lab:** Modul Admin mampu men-generate file `kmeans_rfm.csv`, `fp_growth.csv`, dan `riwayat_pesanan.csv` melalui *endpoint* Django DRF yang langsung terbaca tanpa error di notebook **Google Colab** dan spreadsheet.

---

## 3. Target Pengguna & Konsep Dual-Interface

### A. Pelanggan (Customer)
* **Karakteristik:** Pembeli buket bunga yang menginginkan proses pemesanan praktis tanpa password rumit, cukup menggunakan Username dan Nomor WhatsApp aktif.
* **Pengalaman UI:** Menggunakan bahasa retail kelas atas (*Botanical Atelier*). Hasil kalkulasi *native* FP-Growth dari backend ditampilkan sebagai **"Rekomendasi Spesial Untuk Anda"**, sedangkan hasil klaster K-Means ditampilkan sebagai **"Status Keanggotaan / Tier"** (*Gold*, *Silver*, *Bronze*).
* **Hak Akses Sesi Navigasi Pelanggan:** Dibatasi secara eksklusif hanya pada 2 menu:
  1. **Atelier Crafting:** Studio perangkaian buket bunga 4 dimensi dan banner rekomendasi kombinasi.
  2. **Sreang Club Pass:** Kartu digital keanggotaan, akumulasi poin, target voucher/hadiah, hak istimewa, dan **riwayat aktivitas pesanan personal** milik pelanggan bersangkutan.

### B. Admin / Peneliti (Mahasiswa S1 Teknik Informatika)
* **Karakteristik:** Pengelola operasional florist sekaligus peneliti TA yang membutuhkan kontrol penuh atas pesanan masuk, stok atribut, dan ekstraksi data.
* **Pengalaman UI:** Antarmuka analitis (*Live Analytical Hub*) yang menampilkan metrik evaluasi algoritma secara transparan (Silhouette Score, Support, Confidence, Lift Ratio) serta tombol ekspor dataset CSV untuk kebutuhan pengujian di **Google Colab**.
* **Hak Akses Sesi Navigasi Admin (Hak Akses Penuh):**
  1. **Atelier Crafting & Sreang Club Pass:** Meninjau antarmuka pelanggan dan melakukan simulasi belanja.
  2. **Riwayat Pesanan:** Memantau seluruh antrean transaksi masuk, mengubah status pemesanan, dan **mengekspor seluruh data riwayat transaksi ke format CSV** (`/api/export/orders/`).
  3. **Stok & Inventori:** Mengelola stok fisik bunga/wrap dan penyesuaian harga *price modifier*.
  4. **Live Analytical Hub:** Memantau metrik K-Means dan FP-Growth serta mengunduh dataset TA.

---

## 4. Spesifikasi Kebutuhan Fungsional (Functional Requirements)

### 4.1 Modul Otentikasi Cepat (Berbasis Username & Nomor HP)
* **User Story:** *Sebagai pelanggan, saya ingin mendaftar atau masuk dengan Nama, Username, dan Nomor WhatsApp/HP agar transaksi saya tercatat dan poin loyalty saya terakumulasi secara otomatis tanpa repot mengingat password.*
* **Acceptance Criteria:**
  * Form pelanggan menyediakan input: **Nama Lengkap**, **Username** (unik), dan **Nomor WhatsApp/HP** (unik, disimpan pada tabel `users` SQLite via Django User model).
  * Front-End React mengirim request `POST /api/auth/login/` ke Django DRF; jika data belum ada, sistem otomatis membuat akun pelanggan baru (*quick onboarding*).
  * Tersedia portal terpisah (**Portal Admin**) dengan otentikasi Username/Email & PIN khusus untuk pengelola (`123456`).

### 4.2 Modul Katalog & Studio Kustomisasi (4 Dimensi Atribut)
* **User Story:** *Sebagai pelanggan, saya ingin merangkai buket sesuai selera saya dengan memilih bunga, pembungkus, gaya, dan ukurannya, serta melihat rekomendasi kombinasi terbaik.*
* **Acceptance Criteria:**
  * Pelanggan **wajib** memilih 4 atribut kustomisasi sebelum melanjutkan ke keranjang:
    1. **Jenis Bunga Utama** (Mawar Merah Holland, Krisan Kuning Pompon, Baby's Breath).
    2. **Jenis Bahan Wrap** (Cellophane Matte Transparan, Spunbond Tebal Waterproof).
    3. **Gaya Rangkaian** (Korean Style Wrapping, Classic Round Spiral).
    4. **Ukuran / Kuantitas Tangkai** (Standard 10 Tangkai, Deluxe 18 Tangkai, Grandeur 25 Tangkai).
  * Harga total dihitung secara *real-time* di sisi klien menggunakan React state hooks (*Base Price* Rp 185.000 + *price modifiers*) dan divalidasi ulang oleh Django saat *checkout*.
  * Sistem mengambil *endpoint* `GET /api/catalog/recommendations/` yang ditenagai fungsi **Python Native FP-Growth** di Django untuk menampilkan *banner* **"Rekomendasi Spesial Untuk Anda"** lengkap dengan tombol 1-klik untuk memilih seluruh kombinasi tersebut.

### 4.3 Modul Keranjang & Penjadwalan Pre-Order
* **User Story:** *Sebagai pelanggan, saya ingin menentukan tanggal dan slot jam pengambilan bunga agar bunga dirangkai dalam kondisi segar dan tidak terjadi antrean.*
* **Acceptance Criteria:**
  * Menampilkan ringkasan buket beserta detail 4 atribut yang dipilih.
  * Menyediakan input pemilihan **Tanggal Pickup** dan **Slot Jam Pengambilan** (`09:00 - 10:00 WIB`, `11:00 - 12:00 WIB`, `16:00 - 17:00 WIB`).
  * Menyediakan pilihan tema kartu ucapan (*Birthday*, *Anniversary*, *Graduation*, dll.) dan kolom pesan kartu ucapan (*custom note*).
  * Menyediakan opsi penukaran poin *Sreang Club* untuk potongan harga jika saldo poin mencukupi.
  * Mengirim seluruh payload transaksi melalui `POST /api/orders/` ke Django backend dan menampilkan nota konfirmasi dengan Order ID berformat `#SRG-XXXX`.

### 4.4 Modul Sistem Loyalty (*Sreang Club*)
* **User Story:** *Sebagai pelanggan, saya ingin melihat saldo poin saya, status tier keanggotaan saya, hak istimewa yang saya miliki, serta riwayat pesanan saya.*
* **Acceptance Criteria:**
  * Menampilkan kartu anggota digital (*Sreang Club Pass*) dengan gaya visual elegan sesuai status tier hasil klastering **Python Native K-Means** (*Gold Tier*, *Silver Tier*, *Bronze Tier*).
  * Menampilkan saldo poin aktif dan *progress bar* visual menuju target hadiah utama (Voucher / Hadiah Buket).
  * Poin bertambah secara otomatis di database SQLite melalui *Django Signals* (`post_save` pada model `Order`) **hanya ketika** status pesanan berubah menjadi **"Selesai"** (kelipatan Rp 10.000 = 1 poin).
  * Menampilkan riwayat pesanan personal pelanggan langsung di bawah kartu keanggotaan.

### 4.5 Dashboard Admin & Modul Ekspor Data TA
* **User Story:** *Sebagai admin dan peneliti TA, saya ingin memantau pesanan masuk, mengelola stok atribut, dan mengekspor seluruh dataset CSV untuk diolah dan divisualisasikan di Google Colab.*
* **Acceptance Criteria:**
  * **Manajemen Pesanan:** Mengubah status pesanan (`Menunggu` $\rightarrow$ `Diproses` $\rightarrow$ `Selesai`) via `PATCH /api/orders/{id}/status/`. Perubahan ke `Selesai` secara otomatis memicu injeksi poin loyalitas dan pembaruan segmen RFM K-Means.
  * **Manajemen Inventori:** Memperbarui kuantitas stok fisik dan harga satuan komponen atribut via `PATCH /api/catalog/attributes/{id}/`.
  * **Modul Ekspor Dataset (Django Response CSV Streaming):**
    1. **Ekspor K-Means (`GET /api/export/kmeans/`):** Mengunduh file `kmeans_rfm.csv` berisi kolom `Customer_ID`, `Nama_Pelanggan`, `Recency_Days`, `Frequency_Count`, dan `Monetary_Value`.
    2. **Ekspor FP-Growth (`GET /api/export/fpgrowth/`):** Mengunduh file `fp_growth.csv` berisi `Transaction_ID` dan `Itemsets` (kombinasi atribut per transaksi yang dipisahkan koma) untuk diimpor langsung ke **Google Colab**.
    3. **Ekspor Riwayat Pesanan (`GET /api/export/orders/`):** Mengunduh file `riwayat_pesanan.csv` yang memuat seluruh rincian transaksi operasional florist.

---

## 5. Kebutuhan Non-Fungsional & Standar Desain

* **Portabilitas & Kemudahan Menjalankan:** Penggunaan **Django** dan basis data lokal **SQLite** (`db.sqlite3`) memastikan seluruh backend berjalan secara lokal dengan satu perintah (`python manage.py runserver`) tanpa ketergantungan pada server database eksternal saat sidang TA. Frontend React dijalankan melalui Vite (`npm run dev`) atau disajikan sebagai aset statis terkompilasi.
* **Design System (*Botanical Atelier*):** Menggunakan palet warna *Cypress Forest* (`#143823`), *Golden Amber* (`#E5A93C`), *Crimson Dahlia* (`#B91C1C`), dan *Warm Parchment* (`#FCF9F4`) dengan kombinasi tipografi *Playfair Display* dan *Plus Jakarta Sans*.
* **Integritas Relasional:** Integritas relasional dijaga ketat melalui batasan model Django ORM (`models.ForeignKey(..., on_delete=models.RESTRICT)` dan `CASCADE`), indeks pencarian, serta validasi serializer.
