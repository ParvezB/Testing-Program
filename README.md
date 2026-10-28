# Perbandingan Kinerja Algoritma Apriori vs FP-Growth

Aplikasi desktop berbasis **Python (Flet)** untuk menganalisis pola asosiasi faktor penyebab kecelakaan kapal serta membandingkan kinerja algoritma **Apriori** dan **FP-Growth** dari segi waktu eksekusi, penggunaan memori, dan aturan asosiasi (_association rules_) yang dihasilkan.

---

## ✨ Fitur Utama

- **Upload & Validasi Dataset Excel (`.xlsx` / `.xls`)**:
  - Deteksi otomatis kolom **Nama Kapal** dan kolom-kolom faktor penyebab.
  - Validasi otomatis matriks biner (`0` / `1`) untuk mendeteksi sel kosong atau input tidak valid.
  - Pencarian nama kapal dan paginasi tabel data.
- **Perbandingan Kinerja (Single Run / Multi-Iterasi)**:
  - Menjalankan Apriori dan FP-Growth secara berdampingan dengan parameter _Minimum Support_ dan _Minimum Confidence_ yang dapat diatur.
  - Pengukuran waktu eksekusi rata-rata (_mean_ ± _standar deviasi_ dari 10x pengulangan) dan _peak memory usage_ (`tracemalloc`).
  - Menampilkan _Frequent Itemsets_ dan _Association Rules_ (Support, Confidence, Lift).
- **Uji Multi-Support**:
  - Menguji kedua algoritma pada berbagai nilai _Minimum Support_ sekaligus (misal: `10, 20, 30, 40, 50`) untuk melihat tren perubahan waktu eksekusi dan jumlah rules.
- **Visualisasi Grafik & Observasi Otomatis**:
  - Grafik batang perbandingan waktu eksekusi.
  - Grafik garis tren waktu eksekusi terhadap perubahan _Minimum Support_.
  - Ringkasan observasi otomatis perbandingan kedua algoritma.
- **Export Hasil ke Excel (`.xlsx`)**:
  - Menyimpan hasil perbandingan, detail _association rules_, dan hasil uji multi-support ke dalam file Excel multi-sheet.

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Persiapan Environment

Pastikan **Python 3.10+** sudah terinstal, lalu buat _virtual environment_ (opsional namun disarankan):

```bash
python -m venv .venv
```

Aktifkan _virtual environment_:

- **Windows (PowerShell/CMD):**
  ```bash
  .venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 2. Instalasi Library

Instal semua dependensi yang dibutuhkan dari `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Jalankan Program

Jalankan aplikasi menggunakan perintah berikut:

```bash
python main.py
```

atau menggunakan CLI Flet:

```bash
flet run main.py
```

---

## 📊 Format Dataset Excel

Dataset input berupa file Excel (`.xlsx` / `.xls`) dengan ketentuan:

1. Memiliki kolom identitas kapal (misalnya **`Nama Kapal`**).
2. Kolom-kolom berikutnya adalah faktor penyebab kecelakaan kapal yang berisi nilai biner **`1`** (terjadi/ada) atau **`0`** (tidak terjadi/tidak ada).

---

## 🛠️ Teknologi yang Digunakan

- **[Flet](https://flet.dev/)** — Framework GUI berbasis Flutter untuk Python
- **[mlxtend](https://rasbt.github.io/mlxtend/)** — Implementasi algoritma Apriori, FP-Growth, dan Association Rules
- **[Pandas](https://pandas.pydata.org/) & [OpenPyXL](https://openpyxl.readthedocs.io/)** — Pengolahan data dan ekspor/impor file Excel
- **[Matplotlib](https://matplotlib.org/)** — Visualisasi grafik perbandingan kinerja
