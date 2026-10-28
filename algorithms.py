"""
algorithms.py
--------------
File ini berisi fungsi-fungsi untuk menjalankan algoritma Apriori dan
FP-Growth, sekaligus mengukur kinerjanya (waktu eksekusi & jumlah rules
yang dihasilkan). File ini dipanggil dari main.py (bagian GUI).
"""

import time
import statistics
import tracemalloc
import pandas as pd
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules

# Jumlah pengulangan default saat mengukur waktu eksekusi. Satu kali run saja
# rentan "noise" (proses lain di sistem, caching, dsb), apalagi karena waktu
# eksekusinya sangat kecil (skala milidetik). Dengan mengulang beberapa kali
# dan mengambil rata-ratanya, hasil pengukuran jadi lebih stabil dan bisa
# dipertanggungjawabkan secara metodologis.
DEFAULT_N_RUNS = 10


def prepare_transactions(df: pd.DataFrame, name_col: str, factor_columns: list):
    """
    Menyiapkan data transaksi dari dataframe Excel (matriks biner 0/1)
    menjadi format yang bisa langsung dibaca oleh mlxtend.

    Parameter:
    - df            : dataframe hasil baca Excel
    - name_col      : nama kolom yang berisi nama kapal (tidak ikut dianalisis)
    - factor_columns: daftar kolom faktor kecelakaan (item untuk association rule)

    Return:
    - dataframe berisi HANYA kolom faktor, dengan nilai True/False
      (format wajib yang diminta mlxtend, bukan lagi 0/1)
    """
    transactions_df = df[factor_columns].copy()

    # Ubah semua nilai jadi boolean (True/False), karena mlxtend versi baru
    # mewajibkan format ini, tidak menerima 0/1 dalam bentuk angka biasa
    transactions_df = transactions_df.astype(str) == "1"

    return transactions_df


def validate_transaction_data(df: pd.DataFrame, name_col: str, factor_columns: list):
    """
    Memeriksa apakah kolom faktor di data Excel yang diupload benar-benar
    hanya berisi 0/1 (bukan kosong, bukan teks lain, bukan angka selain 0/1).
    Dipanggil setelah file Excel diupload, SEBELUM data dipakai Apriori/FP-Growth,
    supaya kesalahan input data (misal sel kosong atau salah ketik) ketahuan
    lebih awal daripada diam-diam dianggap "0" oleh program.

    Parameter:
    - df            : dataframe hasil baca Excel
    - name_col      : nama kolom Nama Kapal (dipakai untuk menyebut baris bermasalah)
    - factor_columns: daftar kolom faktor yang harus berisi 0/1

    Return: dict berisi:
    - "is_valid" : True kalau semua kolom faktor bersih (hanya 0/1)
    - "issues"   : list string, masing-masing menjelaskan 1 masalah yang ditemukan
                   (nama kapal, nama kolom, nilai yang salah)
    """
    issues = []

    for col in factor_columns:
        for idx, value in df[col].items():
            # Nilai dianggap valid hanya kalau persis 0 atau 1 (termasuk "0"/"1" dari Excel)
            is_valid_value = str(value).strip() in ("0", "1") and pd.notna(value)

            if not is_valid_value:
                ship_name = df.loc[idx, name_col] if name_col in df.columns else f"baris {idx + 1}"
                if pd.isna(value) or str(value).strip() == "":
                    problem = "kosong"
                else:
                    problem = f"bukan 0/1 (ditemukan: '{value}')"
                issues.append(f"{ship_name} — kolom '{col}': {problem}")

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
    }


def _measure_peak_memory_kb(func):
    """
    Menjalankan func() SEKALI sambil mencatat puncak penggunaan memori
    tambahan (dalam KB) selama proses itu berjalan, memakai modul bawaan
    Python 'tracemalloc'. Dipanggil terpisah dari pengukuran waktu supaya
    overhead tracemalloc tidak ikut mempengaruhi angka waktu eksekusi.
    """
    tracemalloc.start()
    try:
        func()
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return peak / 1024  # byte -> KB


def run_apriori(transactions_df: pd.DataFrame, min_support: float, min_confidence: float,
                 n_runs: int = DEFAULT_N_RUNS):
    """
    Menjalankan algoritma Apriori SEBANYAK n_runs KALI untuk parameter yang
    sama, lalu mengukur statistik waktu eksekusinya (rata-rata, tercepat,
    terlama, dan standar deviasi). Rules & jumlah itemset diambil dari hasil
    run terakhir (nilainya selalu sama di setiap run, karena Apriori adalah
    algoritma deterministik — datanya sama, hasilnya pasti sama).

    Parameter:
    - transactions_df : data transaksi (hasil dari prepare_transactions)
    - min_support      : batas minimum support (misal 0.1 untuk 10%)
    - min_confidence   : batas minimum confidence untuk pembentukan rules
    - n_runs           : jumlah pengulangan untuk pengukuran waktu

    Return: dictionary berisi:
    - "rules"              : dataframe association rules yang ditemukan
    - "execution_time"     : rata-rata waktu eksekusi dari seluruh run (detik)
    - "execution_time_min" : waktu eksekusi tercepat dari seluruh run
    - "execution_time_max" : waktu eksekusi terlama dari seluruh run
    - "execution_time_std" : standar deviasi waktu eksekusi antar run
    - "n_runs"             : jumlah pengulangan yang dilakukan
    - "itemset_count"      : jumlah frequent itemset yang ditemukan
    - "memory_peak_kb"     : puncak penggunaan memori tambahan selama proses (KB)
    """
    times = []
    rules = pd.DataFrame()
    itemset_count = 0

    for _ in range(n_runs):
        start_time = time.perf_counter()

        # Tahap 1: cari frequent itemset (kombinasi faktor yang sering muncul bersama)
        frequent_itemsets = apriori(transactions_df, min_support=min_support, use_colnames=True)

        # Tahap 2: bentuk association rules dari frequent itemset di atas
        if len(frequent_itemsets) > 0:
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        else:
            rules = pd.DataFrame()  # kosong kalau tidak ada itemset yang memenuhi syarat

        end_time = time.perf_counter()
        times.append(end_time - start_time)
        itemset_count = len(frequent_itemsets)

    # Pengukuran memori dilakukan TERPISAH dari loop pengukuran waktu di atas,
    # karena tracemalloc sendiri punya overhead yang bisa membuat angka waktu
    # eksekusi jadi tidak akurat kalau digabung dalam loop yang sama.
    memory_peak_kb = _measure_peak_memory_kb(
        lambda: apriori(transactions_df, min_support=min_support, use_colnames=True)
    )

    return {
        "rules": rules,
        "execution_time": statistics.mean(times),
        "execution_time_min": min(times),
        "execution_time_max": max(times),
        "execution_time_std": statistics.stdev(times) if n_runs > 1 else 0.0,
        "n_runs": n_runs,
        "itemset_count": itemset_count,
        "memory_peak_kb": memory_peak_kb,
    }


def run_fpgrowth(transactions_df: pd.DataFrame, min_support: float, min_confidence: float,
                  n_runs: int = DEFAULT_N_RUNS):
    """
    Menjalankan algoritma FP-Growth SEBANYAK n_runs KALI untuk parameter yang
    sama, lalu mengukur statistik waktu eksekusinya. Struktur parameter &
    return-nya sama persis dengan run_apriori(), supaya mudah dibandingkan
    langsung di main.py.
    """
    times = []
    rules = pd.DataFrame()
    itemset_count = 0

    for _ in range(n_runs):
        start_time = time.perf_counter()

        # Tahap 1: bangun FP-Tree lalu cari frequent itemset (cara kerja beda dari
        # Apriori, tapi hasil frequent itemset-nya seharusnya sama)
        frequent_itemsets = fpgrowth(transactions_df, min_support=min_support, use_colnames=True)

        # Tahap 2: bentuk association rules, sama seperti Apriori
        if len(frequent_itemsets) > 0:
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        else:
            rules = pd.DataFrame()

        end_time = time.perf_counter()
        times.append(end_time - start_time)
        itemset_count = len(frequent_itemsets)

    # Sama seperti run_apriori(): memori diukur terpisah dari loop waktu
    memory_peak_kb = _measure_peak_memory_kb(
        lambda: fpgrowth(transactions_df, min_support=min_support, use_colnames=True)
    )

    return {
        "rules": rules,
        "execution_time": statistics.mean(times),
        "execution_time_min": min(times),
        "execution_time_max": max(times),
        "execution_time_std": statistics.stdev(times) if n_runs > 1 else 0.0,
        "n_runs": n_runs,
        "itemset_count": itemset_count,
        "memory_peak_kb": memory_peak_kb,
    }


def compare_algorithms(df: pd.DataFrame, name_col: str, factor_columns: list,
                        min_support: float, min_confidence: float, n_runs: int = DEFAULT_N_RUNS):
    """
    Fungsi utama yang dipanggil dari main.py: menjalankan Apriori & FP-Growth
    sekaligus (masing-masing diulang n_runs kali untuk pengukuran waktu yang
    lebih stabil), lalu mengembalikan hasil keduanya untuk dibandingkan.
    """
    transactions_df = prepare_transactions(df, name_col, factor_columns)

    apriori_result = run_apriori(transactions_df, min_support, min_confidence, n_runs=n_runs)
    fpgrowth_result = run_fpgrowth(transactions_df, min_support, min_confidence, n_runs=n_runs)

    return {
        "apriori": apriori_result,
        "fpgrowth": fpgrowth_result,
    }


def compare_across_supports(df: pd.DataFrame, name_col: str, factor_columns: list,
                             support_values: list, min_confidence: float, n_runs: int = DEFAULT_N_RUNS):
    """
    Menjalankan compare_algorithms() berulang kali untuk BEBERAPA nilai
    minimum support sekaligus (misal: 5%, 10%, 20%), supaya bisa dilihat
    tren waktu eksekusi & jumlah rules seiring perubahan nilai support.
    Setiap nilai support diukur dari rata-rata n_runs kali percobaan.

    Parameter:
    - support_values : list nilai support dalam desimal, misal [0.05, 0.1, 0.2]
    - min_confidence : nilai confidence yang sama dipakai untuk semua percobaan
    - n_runs         : jumlah pengulangan untuk tiap pengukuran waktu

    Return: list of dict, masing-masing berisi:
    - "support"  : nilai support yang diuji
    - "apriori"  : hasil run_apriori untuk nilai support ini
    - "fpgrowth" : hasil run_fpgrowth untuk nilai support ini
    """
    transactions_df = prepare_transactions(df, name_col, factor_columns)

    results = []
    for support in support_values:
        apriori_result = run_apriori(transactions_df, support, min_confidence, n_runs=n_runs)
        fpgrowth_result = run_fpgrowth(transactions_df, support, min_confidence, n_runs=n_runs)
        results.append({
            "support": support,
            "apriori": apriori_result,
            "fpgrowth": fpgrowth_result,
        })

    return results


def _format_rules_for_export(rules_df: pd.DataFrame):
    """
    Ubah dataframe rules (yang kolom antecedents/consequents-nya berupa
    frozenset) jadi versi yang rapi untuk disimpan ke Excel (teks biasa).
    """
    if len(rules_df) == 0:
        return pd.DataFrame(columns=["antecedents", "consequents", "support", "confidence", "lift"])

    formatted = rules_df.copy()
    formatted["antecedents"] = formatted["antecedents"].apply(lambda x: ", ".join(sorted(x)))
    formatted["consequents"] = formatted["consequents"].apply(lambda x: ", ".join(sorted(x)))
    return formatted[["antecedents", "consequents", "support", "confidence", "lift"]]


def export_results_to_excel(file_path: str, comparison_result: dict,
                             min_support: float, min_confidence: float,
                             multi_results: list = None):
    """
    Menyimpan seluruh hasil perbandingan ke 1 file Excel dengan beberapa sheet,
    supaya bisa langsung dipakai sebagai lampiran skripsi.

    Sheet yang dibuat:
    - "Ringkasan"      : waktu eksekusi & jumlah rules kedua algoritma
    - "Rules_Apriori"  : detail rules dari Apriori
    - "Rules_FPGrowth" : detail rules dari FP-Growth
    - "Multi_Support"  : hasil uji beberapa nilai support (kalau ada)
    """
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # Sheet 1: ringkasan perbandingan (termasuk statistik dari pengulangan run)
        summary_df = pd.DataFrame({
            "Algoritma": ["Apriori", "FP-Growth"],
            "Minimum Support (%)": [min_support * 100, min_support * 100],
            "Minimum Confidence (%)": [min_confidence * 100, min_confidence * 100],
            "Jumlah Pengulangan Run": [
                comparison_result["apriori"]["n_runs"],
                comparison_result["fpgrowth"]["n_runs"],
            ],
            "Waktu Eksekusi Rata-rata (detik)": [
                comparison_result["apriori"]["execution_time"],
                comparison_result["fpgrowth"]["execution_time"],
            ],
            "Waktu Eksekusi Tercepat (detik)": [
                comparison_result["apriori"]["execution_time_min"],
                comparison_result["fpgrowth"]["execution_time_min"],
            ],
            "Waktu Eksekusi Terlama (detik)": [
                comparison_result["apriori"]["execution_time_max"],
                comparison_result["fpgrowth"]["execution_time_max"],
            ],
            "Standar Deviasi Waktu (detik)": [
                comparison_result["apriori"]["execution_time_std"],
                comparison_result["fpgrowth"]["execution_time_std"],
            ],
            "Jumlah Frequent Itemset": [
                comparison_result["apriori"]["itemset_count"],
                comparison_result["fpgrowth"]["itemset_count"],
            ],
            "Jumlah Association Rules": [
                len(comparison_result["apriori"]["rules"]),
                len(comparison_result["fpgrowth"]["rules"]),
            ],
            "Puncak Penggunaan Memori (KB)": [
                comparison_result["apriori"]["memory_peak_kb"],
                comparison_result["fpgrowth"]["memory_peak_kb"],
            ],
        })
        summary_df.to_excel(writer, sheet_name="Ringkasan", index=False)

        # Sheet 2 & 3: detail rules masing-masing algoritma
        _format_rules_for_export(comparison_result["apriori"]["rules"]).to_excel(
            writer, sheet_name="Rules_Apriori", index=False
        )
        _format_rules_for_export(comparison_result["fpgrowth"]["rules"]).to_excel(
            writer, sheet_name="Rules_FPGrowth", index=False
        )

        # Sheet 4 (opsional): hasil uji multi-support, kalau sudah pernah dijalankan
        if multi_results:
            multi_rows = []
            for r in multi_results:
                multi_rows.append({
                    "Minimum Support (%)": r["support"] * 100,
                    "Waktu Apriori (detik)": r["apriori"]["execution_time"],
                    "Rules Apriori": len(r["apriori"]["rules"]),
                    "Memori Apriori (KB)": r["apriori"]["memory_peak_kb"],
                    "Waktu FP-Growth (detik)": r["fpgrowth"]["execution_time"],
                    "Rules FP-Growth": len(r["fpgrowth"]["rules"]),
                    "Memori FP-Growth (KB)": r["fpgrowth"]["memory_peak_kb"],
                })
            pd.DataFrame(multi_rows).to_excel(writer, sheet_name="Multi_Support", index=False)


def generate_observation_summary(multi_results: list):
    """
    Menyusun ringkasan observasi dari hasil uji multi-support, murni berupa
    LAPORAN ANGKA (deskriptif) — tanpa klaim sebab-akibat atau kesimpulan
    yang melebih-lebihkan data, supaya mudah dipertanggungjawabkan saat sidang.

    1. Efisiensi Kecepatan Eksekusi (Runtime) — algoritma mana yang waktunya
       lebih rendah di tiap titik support, dilaporkan apa adanya.
    2. Konsistensi Hasil Aturan (Total Rules) — apakah jumlah rules Apriori
       & FP-Growth sama di tiap titik support, dilaporkan apa adanya.

    Return: dict berisi "runtime_text" dan "consistency_text" (string).
    """
    if not multi_results:
        return {
            "runtime_text": "Belum ada data untuk dianalisis.",
            "consistency_text": "Belum ada data untuk dianalisis.",
        }

    # --- 1. Runtime: hitung berapa kali masing-masing lebih cepat ---
    apriori_faster_count = 0
    fpgrowth_faster_count = 0
    tie_count = 0
    per_point_lines = []

    for r in multi_results:
        support_pct = r["support"] * 100
        t_apriori = r["apriori"]["execution_time"]
        t_fpgrowth = r["fpgrowth"]["execution_time"]

        if t_fpgrowth < t_apriori:
            fpgrowth_faster_count += 1
            label = "FP-Growth lebih rendah"
        elif t_apriori < t_fpgrowth:
            apriori_faster_count += 1
            label = "Apriori lebih rendah"
        else:
            tie_count += 1
            label = "sama"

        per_point_lines.append(
            f"support {support_pct:.0f}%: Apriori {t_apriori:.6f}s, FP-Growth {t_fpgrowth:.6f}s ({label})"
        )

    total_runs = len(multi_results)
    runtime_text = (
        f"Dari {total_runs} nilai minimum support yang diuji, waktu eksekusi FP-Growth lebih rendah pada "
        f"{fpgrowth_faster_count} titik, Apriori lebih rendah pada {apriori_faster_count} titik"
        + (f", dan sama pada {tie_count} titik" if tie_count else "")
        + f". Rincian per titik: " + "; ".join(per_point_lines) + "."
    )

    # --- 2. Konsistensi jumlah rules: laporkan apa adanya ---
    all_consistent = True
    rule_counts_text = []
    for r in multi_results:
        support_pct = r["support"] * 100
        n_apriori = len(r["apriori"]["rules"])
        n_fpgrowth = len(r["fpgrowth"]["rules"])
        if n_apriori != n_fpgrowth:
            all_consistent = False
        rule_counts_text.append(f"support {support_pct:.0f}%: Apriori {n_apriori} rules, FP-Growth {n_fpgrowth} rules")

    rule_counts_summary = "; ".join(rule_counts_text)

    if all_consistent:
        consistency_text = (
            f"Jumlah rules yang dihasilkan Apriori dan FP-Growth sama pada seluruh {total_runs} nilai "
            f"support yang diuji. Rincian: {rule_counts_summary}."
        )
    else:
        consistency_text = (
            f"Jumlah rules yang dihasilkan Apriori dan FP-Growth tidak sama pada sebagian nilai support "
            f"yang diuji. Rincian: {rule_counts_summary}."
        )

    return {
        "runtime_text": runtime_text,
        "consistency_text": consistency_text,
    }