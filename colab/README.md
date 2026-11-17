# Google Colab Data Mining Lab (Tugas Akhir)

Direktori ini dipersiapkan untuk script dan notebook penelitian Tugas Akhir (*Data Mining Lab*) yang mengolah dataset hasil ekspor dari modul Admin Sreang Florist:

1. **`kmeans_rfm.csv`**:
   - Kolom: `Customer_ID`, `Nama_Pelanggan`, `Recency_Days`, `Frequency_Count`, `Monetary_Value`
   - Algoritma: **K-Means Clustering** (dengan Elbow Method, Silhouette Score, Davies-Bouldin Index) untuk segmentasi pelanggan.

2. **`fp_growth.csv`**:
   - Kolom: `Transaction_ID`, `Itemsets`
   - Algoritma: **FP-Growth Association Rule Mining** (Support, Confidence, Lift Ratio) untuk penemuan pola kombinasi buket favorit.
