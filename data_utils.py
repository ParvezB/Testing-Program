"""
data_utils.py
--------------
Kumpulan fungsi bantu "polos" (tidak bergantung ke Flet sama sekali),
jadi gampang dites/dipahami terpisah dari urusan tampilan.

Isinya 2 kelompok:
1. Deteksi kolom "Nama Kapal" dari header Excel yang mungkin
   penulisannya bervariasi (Fitur #5).
2. Validasi nilai persen (Minimum Support/Confidence) yang diketik
   user, supaya tetap di rentang 0-100 (Fitur #4).
"""

# Variasi nama kolom "nama kapal" yang sudah diketahui/sering dipakai.
# Ini jadi acuan utama sebelum dicoba pencocokan yang lebih longgar.
NAME_COL_CANDIDATES = {"Nama Kapal", "nama kapal", "Nama_Kapal"}


def normalize_column_name(name: str) -> str:
    """
    Merapikan nama kolom supaya mudah dibandingkan:
    - underscore diubah jadi spasi ("Nama_Kapal" -> "Nama Kapal")
    - spasi berlebih dirapikan jadi 1 spasi
    - semua huruf diubah jadi huruf kecil

    Dipakai sebelum membandingkan nama kolom, supaya variasi penulisan
    seperti "NAMA KAPAL", "Nama_Kapal ", "nama   kapal" tetap dikenali sama.
    """
    return " ".join(str(name).replace("_", " ").split()).lower()


def detect_name_column(columns):
    """
    Mencari kolom mana di file Excel yang berisi nama kapal.

    Fitur #5: sebelumnya program hanya mengenali kolom kalau namanya
    PERSIS SAMA dengan salah satu dari NAME_COL_CANDIDATES. Kalau header
    di Excel user sedikit beda (spasi ekstra, huruf besar semua, pakai
    underscore, dst), program bisa salah menebak kolom lain sebagai
    "nama kapal" tanpa pemberitahuan apa pun ke user.

    Strategi pencarian (dari paling ketat ke paling longgar):
    1. Cocokkan PERSIS setelah dinormalisasi (lihat normalize_column_name)
    2. Kalau belum ketemu, cari kolom yang mengandung kata "nama" DAN
       "kapal" sekaligus (urutan kata bebas)
    3. Kalau masih belum ketemu, pakai kolom pertama sebagai fallback
       (perilaku lama tetap dipertahankan sebagai jaga-jaga terakhir)
    """
    normalized_candidates = {normalize_column_name(c) for c in NAME_COL_CANDIDATES}

    # Tahap 1: cocokkan persis (setelah dinormalisasi)
    for col in columns:
        if normalize_column_name(col) in normalized_candidates:
            return col

    # Tahap 2: cocokkan longgar, kolom yang mengandung kata
    # "nama" dan "kapal" sekaligus
    for col in columns:
        normalized = normalize_column_name(col)
        if "nama" in normalized and "kapal" in normalized:
            return col

    # Tahap 3: fallback ke kolom pertama
    return columns[0]


def parse_percent_field(raw_value: str, field_label: str):
    """
    Memvalidasi 1 nilai persen yang diketik user (misal untuk field
    Minimum Support atau Minimum Confidence).

    Fitur #4: memastikan nilainya DUA hal sekaligus:
    - berupa angka yang valid (bukan teks kosong/salah ketik)
    - berada di rentang masuk akal 0-100

    Tanpa ini, program akan diam-diam menghasilkan hasil yang tidak
    masuk akal kalau user salah ketik (misal "150" atau "-5").

    Return: (nilai_desimal, pesan_error)
    - Kalau valid: nilai_desimal berisi hasil bagi 100 (misal 10 -> 0.1),
      pesan_error berisi None.
    - Kalau tidak valid: nilai_desimal berisi None, pesan_error berisi
      alasannya (siap ditampilkan langsung ke user).
    """
    try:
        value_percent = float(raw_value)
    except (TypeError, ValueError):
        return None, f"{field_label} harus berupa angka."

    if value_percent < 0 or value_percent > 100:
        return None, f"{field_label} harus di antara 0 dan 100 (yang dimasukkan: {raw_value})."

    return value_percent / 100, None