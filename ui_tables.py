"""
ui_tables.py
------------
Fungsi-fungsi pembuat tabel (ft.DataTable) yang dipakai di beberapa
tempat berbeda di aplikasi:

- build_table()              -> tabel preview data kapal (halaman utama)
- build_rules_table_content() -> tabel detail association rules (di dalam modal)
- build_multi_support_table() -> tabel ringkasan hasil uji multi-support

Semua fungsi di sini menerima data sebagai PARAMETER BIASA (bukan lewat
closure/state global), supaya gampang dipakai ulang dan gampang dites
terpisah dari main.py.
"""

import flet as ft
import pandas as pd


def build_table(df_page: pd.DataFrame, start_index: int, name_col: str, factor_columns: list):
    """
    Bangun 1 tabel untuk 1 halaman data kapal (dipakai bersama fitur
    pagination di main.py).

    - df_page: potongan dataframe yang mau ditampilkan di halaman ini saja
    - start_index: nomor urut awal (dipakai untuk mengisi kolom "No")
    - name_col: nama kolom yang berisi nama kapal
    - factor_columns: daftar nama kolom faktor/jenis kecelakaan (0/1)
    """
    columns = [
        ft.DataColumn(ft.Container(ft.Text("No", weight=ft.FontWeight.BOLD), width=40)),
        ft.DataColumn(ft.Container(ft.Text("Nama Kapal", weight=ft.FontWeight.BOLD), width=160)),
    ]
    for col in factor_columns:
        header_label = col.replace("_", " ")
        columns.append(
            ft.DataColumn(
                ft.Container(
                    ft.Text(header_label, weight=ft.FontWeight.BOLD, size=12),
                    width=140,
                )
            )
        )

    rows = []
    for offset, (_, row) in enumerate(df_page.iterrows()):
        row_no = start_index + offset + 1
        cells = [
            ft.DataCell(ft.Container(ft.Text(str(row_no)), width=40)),
            ft.DataCell(ft.Container(ft.Text(str(row[name_col])), width=160)),
        ]
        for col in factor_columns:
            value = row[col]
            is_true = str(value) == "1"
            badge = ft.Container(
                content=ft.Text(
                    "Ya" if is_true else "-",
                    size=12,
                    color=ft.Colors.WHITE if is_true else ft.Colors.GREY_500,
                    weight=ft.FontWeight.BOLD if is_true else ft.FontWeight.NORMAL,
                ),
                bgcolor=ft.Colors.RED_400 if is_true else None,
                padding=ft.Padding(top=4, bottom=4, left=10, right=10),
                border_radius=6,
                width=140,
                alignment=ft.Alignment.CENTER,
            )
            cells.append(ft.DataCell(badge))
        rows.append(ft.DataRow(cells=cells))

    data_table = ft.DataTable(
        columns=columns,
        rows=rows,
        column_spacing=14,
        heading_row_color=ft.Colors.GREY_800,
        heading_row_height=54,
        data_row_min_height=48,
        data_row_max_height=48,
        divider_thickness=0.4,
        border_radius=10,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

    # Dibungkus Row dengan scroll horizontal supaya tabel tetap rapi
    # baik saat window di-minimize (bisa discroll) maupun di-maximize (tidak pecah)
    return ft.Row(
        controls=[data_table],
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
    )


def build_rules_table_content(rules_df: pd.DataFrame, title: str):
    """
    Bangun tabel isi association rules (antecedent -> consequent beserta
    support/confidence/lift) untuk ditampilkan di dalam modal "Detail Rules".
    """
    if len(rules_df) == 0:
        return ft.Text(f"Tidak ada rules yang ditemukan untuk {title}.", color=ft.Colors.GREY_500)

    # Kolom "antecedents"/"consequents" dari mlxtend berupa frozenset,
    # perlu diubah dulu jadi teks biasa (dipisah koma) supaya bisa ditampilkan
    def format_itemset(itemset):
        return ", ".join(sorted(itemset))

    columns = [
        ft.DataColumn(ft.Container(ft.Text("Jika (Antecedent)", weight=ft.FontWeight.BOLD, size=12), width=260)),
        ft.DataColumn(ft.Container(ft.Text("Maka (Consequent)", weight=ft.FontWeight.BOLD, size=12), width=260)),
        ft.DataColumn(ft.Container(ft.Text("Support", weight=ft.FontWeight.BOLD, size=12), width=90)),
        ft.DataColumn(ft.Container(ft.Text("Confidence", weight=ft.FontWeight.BOLD, size=12), width=90)),
        ft.DataColumn(ft.Container(ft.Text("Lift", weight=ft.FontWeight.BOLD, size=12), width=90)),
    ]

    rows = []
    for _, r in rules_df.iterrows():
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Container(ft.Text(format_itemset(r["antecedents"]), size=12), width=260, padding=ft.Padding(top=8, bottom=8, left=0, right=0))),
                    ft.DataCell(ft.Container(ft.Text(format_itemset(r["consequents"]), size=12), width=260, padding=ft.Padding(top=8, bottom=8, left=0, right=0))),
                    ft.DataCell(ft.Container(ft.Text(f"{r['support']:.3f}", size=12), width=90)),
                    ft.DataCell(ft.Container(ft.Text(f"{r['confidence']:.3f}", size=12), width=90)),
                    ft.DataCell(ft.Container(ft.Text(f"{r['lift']:.3f}", size=12), width=90)),
                ]
            )
        )

    data_table = ft.DataTable(
        columns=columns,
        rows=rows,
        column_spacing=14,
        heading_row_color=ft.Colors.GREY_800,
        heading_row_height=44,
        # Tinggi baris TIDAK dibatasi (biarkan menyesuaikan isi), karena
        # beberapa baris punya kombinasi banyak faktor yang wrap jadi 2-3 baris teks
        divider_thickness=0.4,
        border_radius=10,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

    # Modal punya tinggi TETAP, jadi di sini perlu scroll 2 arah sendiri
    # (beda dengan tabel di halaman utama yang mengandalkan scroll halaman)
    return ft.Column(
        [ft.Row([data_table], scroll=ft.ScrollMode.ALWAYS)],
        scroll=ft.ScrollMode.ALWAYS,
        expand=True,
    )


def build_multi_support_table(multi_results: list):
    """
    Bangun tabel ringkasan hasil uji multi-support: 1 baris per nilai
    minimum support yang diuji, dengan kolom waktu, jumlah rules, dan
    pemakaian memori untuk masing-masing algoritma.
    """
    # Ambil jumlah pengulangan run dari hasil pertama (semua titik support
    # memakai n_runs yang sama), untuk ditulis di header kolom waktu
    n_runs = multi_results[0]["apriori"]["n_runs"] if multi_results else 1

    columns = [
        ft.DataColumn(ft.Container(ft.Text("Support", weight=ft.FontWeight.BOLD, size=12), width=80)),
        ft.DataColumn(ft.Container(ft.Text(f"Waktu Apriori (rata² {n_runs}x)", weight=ft.FontWeight.BOLD, size=12), width=140)),
        ft.DataColumn(ft.Container(ft.Text("Rules Apriori", weight=ft.FontWeight.BOLD, size=12), width=100)),
        ft.DataColumn(ft.Container(ft.Text("Memori Apriori (KB)", weight=ft.FontWeight.BOLD, size=12), width=130)),
        ft.DataColumn(ft.Container(ft.Text(f"Waktu FP-Growth (rata² {n_runs}x)", weight=ft.FontWeight.BOLD, size=12), width=160)),
        ft.DataColumn(ft.Container(ft.Text("Rules FP-Growth", weight=ft.FontWeight.BOLD, size=12), width=130)),
        ft.DataColumn(ft.Container(ft.Text("Memori FP-Growth (KB)", weight=ft.FontWeight.BOLD, size=12), width=150)),
    ]

    rows = []
    for r in multi_results:
        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Container(ft.Text(f"{r['support'] * 100:.0f}%", size=12), width=80)),
                    ft.DataCell(ft.Container(ft.Text(f"{r['apriori']['execution_time']:.6f}s", size=12), width=140)),
                    ft.DataCell(ft.Container(ft.Text(str(len(r["apriori"]["rules"])), size=12), width=100)),
                    ft.DataCell(ft.Container(ft.Text(f"{r['apriori']['memory_peak_kb']:.2f}", size=12), width=130)),
                    ft.DataCell(ft.Container(ft.Text(f"{r['fpgrowth']['execution_time']:.6f}s", size=12), width=160)),
                    ft.DataCell(ft.Container(ft.Text(str(len(r["fpgrowth"]["rules"])), size=12), width=130)),
                    ft.DataCell(ft.Container(ft.Text(f"{r['fpgrowth']['memory_peak_kb']:.2f}", size=12), width=150)),
                ]
            )
        )

    data_table = ft.DataTable(
        columns=columns,
        rows=rows,
        column_spacing=14,
        heading_row_color=ft.Colors.GREY_800,
        heading_row_height=44,
        divider_thickness=0.4,
        border_radius=10,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

    return ft.Row([data_table], scroll=ft.ScrollMode.ALWAYS, expand=True)