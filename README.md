# Perbandingan Kinerja Algoritma Apriori vs FP-Growth

Aplikasi desktop berbasis **Python (Flet)** untuk menganalisis pola asosiasi faktor penyebab kecelakaan kapal serta membandingkan kinerja algoritma **Apriori** dan **FP-Growth** dari segi waktu eksekusi, penggunaan memori, dan aturan asosiasi (*association rules*) yang dihasilkan.

---

## ✨ Fitur Utama

- **Upload & Validasi Dataset Excel (`.xlsx` / `.xls`)**:
  - Deteksi otomatis kolom **Nama Kapal** dan kolom-kolom faktor penyebab.
  - Validasi otomatis matriks biner (`0` / `1`) untuk mendeteksi sel kosong atau input tidak valid.
  - Pencarian nama kapal dan paginasi tabel data.
- **Perbandingan Kinerja (Single Run / Multi-Iterasi)**:
  - Menjalankan Apriori dan FP-Growth secara berdampingan dengan parameter *Minimum Support* dan *Minimum Confidence* yang dapat diatur.
  - Pengukuran waktu eksekusi rata-rata (*mean* ± *standar deviasi* dari 10x pengulangan) dan *peak memory usage* (`tracemalloc`).
  - Menampilkan *Frequent Itemsets* dan *Association Rules* (Support, Confidence, Lift).
- **Uji Multi-Support**:
  - Menguji kedua algoritma pada berbagai nilai *Minimum Support* sekaligus (misal: `10, 20, 30, 40, 50`) untuk melihat tren perubahan waktu eksekusi dan jumlah rules.
- **Visualisasi Grafik & Observasi Otomatis**:
  - Grafik batang perbandingan waktu eksekusi.
  - Grafik garis tren waktu eksekusi terhadap perubahan *Minimum Support*.
  - Ringkasan observasi otomatis perbandingan kedua algoritma.
- **Export Hasil ke Excel (`.xlsx`)**:
  - Menyimpan hasil perbandingan, detail *association rules*, dan hasil uji multi-support ke dalam file Excel multi-sheet.

---

## 📁 Struktur File

```text
├── main.py            # Entry point aplikasi GUI (state, event handler, layout Flet)
├── algorithms.py      # Logika Apriori & FP-Growth, pengukuran waktu/memori, validasi, export Excel
├── data_utils.py      # Fungsi utilitas deteksi kolom nama kapal & validasi input persen
├── charts.py          # Pembuatan grafik perbandingan dan tren menggunakan Matplotlib
├── ui_tables.py       # Komponen pembuatan tabel data dan tabel hasil (ft.DataTable)
├── ui_dialogs.py      # Komponen modal/dialog detail rules, grafik, dan kartu ringkasan
└── requirements.txt   # Daftar dependensi library Python
```

---

## 🚀 Cara Menjalankan Aplikasi

### 1. Persiapan Environment
Pastikan **Python 3.10+** sudah terinstal, lalu buat *virtual environment* (opsional namun disarankan):

```bash
python -m venv .venv
```

Aktifkan *virtual environment*:
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

