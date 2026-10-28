"""
charts.py
---------
Fungsi-fungsi pembuat grafik (matplotlib) untuk membandingkan kinerja
Apriori vs FP-Growth.

Setiap fungsi di sini menerima data hasil perhitungan (dict/list biasa,
BUKAN objek Flet), lalu mengembalikan gambar grafik dalam bentuk bytes
PNG mentah. Bytes ini nantinya dipakai langsung sebagai isi
`ft.Image(src=...)` oleh kode UI (lihat ui_dialogs.py), tanpa perlu
disimpan ke file atau diubah ke base64.

Dipisah ke file sendiri karena logikanya murni "olah data -> gambar",
tidak ada urusan tampilan/state Flet sama sekali.
"""

import io
import matplotlib
matplotlib.use("Agg")  # mode tanpa GUI, supaya matplotlib tidak buka window sendiri
import matplotlib.pyplot as plt


def _figure_to_png_bytes(fig) -> bytes:
    """Helper kecil: ubah 1 figure matplotlib jadi bytes PNG, lalu tutup figure-nya."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)  # tutup figure supaya tidak menumpuk di memori
    buffer.seek(0)
    return buffer.read()


def build_comparison_chart_bytes(apriori_result: dict, fpgrowth_result: dict) -> bytes:
    """
    Bikin grafik BATANG (bar chart) yang membandingkan waktu eksekusi
    rata-rata Apriori vs FP-Growth untuk satu parameter yang sama.

    Dipakai saat tombol "Grafik Perbandingan" di salah satu kartu hasil diklik.
    """
    labels = ["Apriori", "FP-Growth"]
    times = [apriori_result["execution_time"], fpgrowth_result["execution_time"]]
    colors = ["#FB923C", "#22D3EE"]  # oranye untuk Apriori, cyan untuk FP-Growth

    # Siapkan figure dengan tema gelap supaya menyatu dengan tampilan aplikasi
    fig, ax = plt.subplots(figsize=(6, 4), facecolor="#212121")
    ax.set_facecolor("#212121")

    bars = ax.bar(labels, times, color=colors, width=0.5)

    # Tulis angka waktu eksekusi di atas tiap bar
    for bar, t in zip(bars, times):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{t:.6f}s",
            ha="center",
            va="bottom",
            color="white",
            fontsize=10,
        )

    ax.set_title("Perbandingan Waktu Eksekusi", color="white", fontsize=13)
    ax.set_ylabel("Waktu (detik)", color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#555555")

    fig.tight_layout()
    return _figure_to_png_bytes(fig)


def build_trend_chart_bytes(multi_results: list) -> bytes:
    """
    Bikin grafik GARIS (line chart) yang menunjukkan tren waktu eksekusi
    Apriori vs FP-Growth seiring perubahan nilai minimum support.

    Dipakai saat tombol "Lihat Grafik Tren" (hasil uji multi-support) diklik.
    `multi_results` adalah list hasil dari algorithms.compare_across_supports().
    """
    supports_percent = [r["support"] * 100 for r in multi_results]
    apriori_times = [r["apriori"]["execution_time"] for r in multi_results]
    fpgrowth_times = [r["fpgrowth"]["execution_time"] for r in multi_results]

    fig, ax = plt.subplots(figsize=(6.5, 4.2), facecolor="#212121")
    ax.set_facecolor("#212121")

    ax.plot(supports_percent, apriori_times, marker="o", color="#FB923C", label="Apriori")
    ax.plot(supports_percent, fpgrowth_times, marker="o", color="#22D3EE", label="FP-Growth")

    ax.set_title("Tren Waktu Eksekusi vs Minimum Support", color="white", fontsize=13)
    ax.set_xlabel("Minimum Support (%)", color="white")
    ax.set_ylabel("Waktu Eksekusi (detik)", color="white")
    ax.tick_params(colors="white")
    ax.legend(facecolor="#2b2b2b", labelcolor="white")
    for spine in ax.spines.values():
        spine.set_color("#555555")

    fig.tight_layout()
    return _figure_to_png_bytes(fig)