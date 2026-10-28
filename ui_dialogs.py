"""
ui_dialogs.py
-------------
Fungsi-fungsi pembuat MODAL/DIALOG (ft.AlertDialog) dan kartu ringkasan
hasil, yaitu bagian-bagian UI yang muncul setelah tombol tertentu diklik:

- build_result_card()      -> 1 kartu ringkasan hasil (Apriori / FP-Growth)
- open_rules_dialog()      -> modal tabel detail association rules
- open_chart_dialog()      -> modal grafik batang perbandingan waktu
- open_trend_dialog()      -> modal grafik garis tren waktu vs support
- open_observation_dialog() -> modal ringkasan observasi (2 kotak teks)

Setiap fungsi "open_..." menerima `page` sebagai parameter (bukan lewat
closure), supaya file ini berdiri sendiri dan bisa dipanggil dari
main.py dengan page yang sedang aktif.
"""

import flet as ft

import algorithms
import charts
import ui_tables


def open_rules_dialog(page: ft.Page, rules_df, title: str):
    """
    Dipanggil saat tombol "Detail Rules" di salah satu kartu diklik.
    Membuka modal (AlertDialog) berisi tabel rules algoritma terkait.
    """
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(f"Detail Rules — {title} ({len(rules_df)} rules)"),
        content=ft.Container(
            content=ui_tables.build_rules_table_content(rules_df, title),
            width=850,
            height=450,
        ),
        actions=[
            ft.TextButton("Kembali", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)


def open_chart_dialog(page: ft.Page, apriori_result: dict, fpgrowth_result: dict):
    """
    Dipanggil saat tombol "Grafik Perbandingan" diklik.
    Membuka modal berisi grafik bar waktu eksekusi Apriori vs FP-Growth.
    """
    chart_bytes = charts.build_comparison_chart_bytes(apriori_result, fpgrowth_result)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Grafik Perbandingan Kinerja"),
        content=ft.Container(
            content=ft.Image(src=chart_bytes, width=550, height=380, fit=ft.BoxFit.CONTAIN),
            width=580,
            height=400,
        ),
        actions=[
            ft.TextButton("Kembali", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)


def open_trend_dialog(page: ft.Page, multi_results: list):
    """
    Dipanggil saat tombol "Lihat Grafik Tren" (hasil uji multi-support) diklik.
    Membuka modal berisi grafik garis tren waktu eksekusi vs minimum support.
    """
    chart_bytes = charts.build_trend_chart_bytes(multi_results)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Grafik Tren Waktu vs Minimum Support"),
        content=ft.Container(
            content=ft.Image(src=chart_bytes, width=580, height=400, fit=ft.BoxFit.CONTAIN),
            width=610,
            height=420,
        ),
        actions=[
            ft.TextButton("Kembali", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)


def build_observation_box(number_title: str, body_text: str):
    """Bangun 1 kotak observasi (dipakai 2x: Runtime & Konsistensi)."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(number_title, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_300),
                ft.Text(body_text, size=12, color=ft.Colors.GREY_300, selectable=True),
            ],
            spacing=8,
        ),
        bgcolor=ft.Colors.GREY_800,
        border_radius=10,
        padding=16,
        border=ft.Border.all(1, ft.Colors.GREY_700),
        expand=True,
    )


def open_observation_dialog(page: ft.Page, multi_results: list):
    """
    Dipanggil saat tombol "Lihat Ringkasan Observasi" diklik.
    Membuat 2 kotak: Efisiensi Runtime & Konsistensi Hasil Aturan,
    dengan teks yang murni melaporkan angka dari algorithms.generate_observation_summary.
    """
    summary = algorithms.generate_observation_summary(multi_results)

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row(
            [
                ft.Icon(ft.Icons.INSIGHTS, color=ft.Colors.CYAN_300, size=20),
                ft.Text("Ringkasan Observasi Algoritma", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.Text("Auto-Evaluated", size=11, color=ft.Colors.GREY_500, italic=True),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Row(
                [
                    build_observation_box("1. Efisiensi Kecepatan Eksekusi (Runtime):", summary["runtime_text"]),
                    build_observation_box("2. Konsistensi Hasil Aturan (Total Rules):", summary["consistency_text"]),
                ],
                spacing=16,
            ),
            width=900,
            height=280,
        ),
        actions=[
            ft.TextButton("Kembali", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dialog)


def build_result_card(page: ft.Page, title: str, result: dict, color, other_result: dict):
    """
    Bangun 1 kartu ringkasan hasil untuk 1 algoritma (dipakai 2x:
    untuk Apriori dan untuk FP-Growth). Kartu ini berisi statistik
    (waktu eksekusi, jumlah itemset/rules, pemakaian memori) di kiri,
    dan 2 tombol ("Detail Rules" & "Grafik Perbandingan") di kanan yang
    membuka modal lewat open_rules_dialog()/open_chart_dialog() di atas.
    """
    # Bagian kiri: judul + statistik (waktu eksekusi, itemset, rules)
    stats_column = ft.Column(
        [
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"Waktu eksekusi (rata-rata {result['n_runs']}x run): {result['execution_time']:.6f} detik",
                size=13,
            ),
            ft.Text(
                f"Tercepat: {result['execution_time_min']:.6f} detik  |  "
                f"Terlama: {result['execution_time_max']:.6f} detik",
                size=12,
                color=ft.Colors.GREY_400,
            ),
            ft.Text(f"Jumlah frequent itemset: {result['itemset_count']}", size=13),
            ft.Text(f"Jumlah association rules: {len(result['rules'])}", size=13),
            ft.Text(f"Puncak penggunaan memori: {result['memory_peak_kb']:.2f} KB", size=13),
        ],
        spacing=6,
        expand=True,
    )

    # Bagian kanan: kedua tombol disusun ke bawah, sejajar mulai dari atas
    # (sejajar dengan baris "Waktu eksekusi"), bukan menumpuk di bawah teks
    buttons_column = ft.Column(
        [
            ft.Button(
                "Detail Rules",
                icon=ft.Icons.TABLE_CHART,
                on_click=lambda e: open_rules_dialog(page, result["rules"], title),
            ),
            ft.Button(
                "Grafik Perbandingan",
                icon=ft.Icons.BAR_CHART,
                # Grafik selalu membandingkan Apriori vs FP-Growth sekaligus,
                # jadi butuh hasil kedua algoritma (result & other_result)
                on_click=lambda e: open_chart_dialog(
                    page,
                    result if title == "Apriori" else other_result,
                    other_result if title == "Apriori" else result,
                ),
            ),
        ],
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.END,
    )

    return ft.Container(
        content=ft.Row(
            [stats_column, buttons_column],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor=ft.Colors.GREY_800,
        border_radius=10,
        padding=16,
        border=ft.Border.all(1, color),
        expand=True,
    )