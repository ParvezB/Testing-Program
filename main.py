"""
main.py
-------
Entry point aplikasi (jalankan file ini: `flet run main.py` / `python main.py`).

File ini isinya cuma 3 hal:
1. STATE & UI CONTROLS — variabel yang menyimpan data aplikasi & elemen
   input (tombol, text field, tabel, dsb).
2. EVENT HANDLER — fungsi yang dipanggil saat tombol diklik (upload file,
   jalankan perbandingan, export, dsb). Logika berat (bikin tabel, grafik,
   modal) sudah dipindah ke file lain dan tinggal dipanggil dari sini.
3. LAYOUT — menyusun semua UI control di atas jadi 1 halaman.

Modul lain yang dipakai:
- algorithms.py  -> logika Apriori/FP-Growth, validasi data, export Excel
- data_utils.py  -> deteksi kolom nama kapal & validasi input persen
- charts.py      -> pembuat grafik matplotlib
- ui_tables.py   -> pembuat tabel (ft.DataTable)
- ui_dialogs.py  -> pembuat modal/dialog & kartu ringkasan hasil
"""

import flet as ft
import pandas as pd
import math

import algorithms
import data_utils
import ui_tables
import ui_dialogs


def main(page: ft.Page):
    page.title = "Perbandingan Kinerja Apriori vs FP-Growth"
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.GREY_900

    DEFAULT_PAGE_SIZE = "5"

    # ---------------------------------------------------------------
    # STATE
    # ---------------------------------------------------------------
    state = {
        "df": None,           # dataframe asli hasil baca Excel
        "filtered_df": None,  # dataframe setelah kena search
        "page": 0,            # halaman aktif (mulai dari 0)
        "page_size": 5,        # jumlah baris per halaman
        "factor_columns": [],  # daftar kolom faktor kecelakaan (di luar Nama Kapal)
        "name_col": None,
        "last_comparison": None,    # hasil terakhir dari "Jalankan Perbandingan"
        "last_multi_results": None, # hasil terakhir dari "Jalankan Uji Multi-Support"
    }

    # ---------------------------------------------------------------
    # UI CONTROLS
    # ---------------------------------------------------------------
    status_text = ft.Text(value="Belum ada file yang dipilih.", color=ft.Colors.GREY_400)

    # Banner peringatan validasi data (muncul kalau ada sel kosong/bukan 0-1
    # di kolom faktor setelah file Excel diupload)
    validation_banner = ft.Container(visible=False)

    table_container = ft.Column()
    page_label = ft.Text("", color=ft.Colors.GREY_400, size=13)

    search_field = ft.TextField(
        label="Cari Nama Kapal",
        prefix_icon=ft.Icons.SEARCH,
        width=260,
        dense=True,
        border_radius=8,
        visible=False,
    )

    page_size_dropdown = ft.Dropdown(
        label="Data per halaman",
        width=160,
        dense=True,
        border_radius=8,
        options=[ft.dropdown.Option("5"), ft.dropdown.Option("10")],
        value=DEFAULT_PAGE_SIZE,
        visible=False,
    )

    search_button = ft.Button(
        "Cari",
        icon=ft.Icons.SEARCH,
        visible=False,
    )

    prev_button = ft.IconButton(icon=ft.Icons.CHEVRON_LEFT, visible=False)
    next_button = ft.IconButton(icon=ft.Icons.CHEVRON_RIGHT, visible=False)

    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=ft.Colors.WHITE,
        bgcolor=ft.Colors.BLUE_600,
        tooltip="Refresh tampilan",
    )

    # Input parameter untuk algoritma Apriori & FP-Growth.
    # Nilai diisi dalam bentuk persen (%) supaya lebih mudah dipahami user,
    # nanti saat dipakai akan dikonversi jadi desimal (misal 10% -> 0.1)
    min_support_field = ft.TextField(
        label="Minimum Support (%)",
        value="10",
        width=200,
        dense=True,
        border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False,
    )

    min_confidence_field = ft.TextField(
        label="Minimum Confidence (%)",
        value="50",
        width=200,
        dense=True,
        border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False,
    )

    # Tombol untuk menjalankan Apriori & FP-Growth sekaligus, memanggil
    # fungsi compare_algorithms() dari algorithms.py
    run_button = ft.Button(
        "Jalankan Perbandingan",
        icon=ft.Icons.PLAY_ARROW,
        visible=False,
    )

    # Tempat menampilkan ringkasan hasil (waktu eksekusi & jumlah rules)
    # setelah tombol "Jalankan Perbandingan" diklik
    results_container = ft.Column()

    # Input daftar nilai minimum support yang mau diuji sekaligus,
    # dipisahkan koma (misal: "5,10,20" berarti uji 3 nilai: 5%, 10%, 20%)
    multi_support_field = ft.TextField(
        label="Daftar Minimum Support (%), pisahkan koma",
        value="5,10,20",
        width=320,
        dense=True,
        border_radius=8,
        visible=False,
    )

    multi_run_button = ft.Button(
        "Jalankan Uji Multi-Support",
        icon=ft.Icons.TIMELINE,
        visible=False,
    )

    # Tempat menampilkan tabel ringkasan hasil uji multi-support
    multi_results_container = ft.Column()

    # Tombol untuk export seluruh hasil (ringkasan + rules + multi-support)
    # ke 1 file Excel, supaya bisa langsung dilampirkan ke skripsi
    export_button = ft.Button(
        "Export Hasil ke Excel",
        icon=ft.Icons.DOWNLOAD,
        visible=False,
    )
    export_status_text = ft.Text("", size=12)

    # ---------------------------------------------------------------
    # HELPER: render halaman aktif (pakai ui_tables.build_table)
    # ---------------------------------------------------------------
    def render_page():
        df_filtered = state["filtered_df"]

        if df_filtered is None:
            table_container.controls = []
            page_label.value = ""
            page.update()
            return

        total_rows = len(df_filtered)
        page_size = state["page_size"]
        total_pages = max(1, math.ceil(total_rows / page_size))

        if state["page"] >= total_pages:
            state["page"] = total_pages - 1
        if state["page"] < 0:
            state["page"] = 0

        start = state["page"] * page_size
        end = start + page_size
        df_page = df_filtered.iloc[start:end]

        if total_rows == 0:
            table_container.controls = [
                ft.Container(
                    content=ft.Text("Tidak ada data yang cocok dengan pencarian.", color=ft.Colors.GREY_500),
                    padding=20,
                )
            ]
        else:
            table_container.controls = [
                ui_tables.build_table(df_page, start, state["name_col"], state["factor_columns"])
            ]

        page_label.value = f"Halaman {state['page'] + 1} dari {total_pages}  •  {total_rows} data ditemukan"
        prev_button.disabled = state["page"] <= 0
        next_button.disabled = state["page"] >= total_pages - 1

        page.update()

    # ---------------------------------------------------------------
    # HELPER: terapkan search + page size (dipicu tombol "Cari")
    # ---------------------------------------------------------------
    def apply_search(e=None):
        df = state["df"]
        if df is None:
            return

        result = df
        keyword = (search_field.value or "").strip().lower()
        if keyword:
            result = result[result[state["name_col"]].astype(str).str.lower().str.contains(keyword)]

        state["filtered_df"] = result
        state["page_size"] = int(page_size_dropdown.value)
        state["page"] = 0
        render_page()

    def on_prev_click(e):
        state["page"] -= 1
        render_page()

    def on_next_click(e):
        state["page"] += 1
        render_page()

    def on_refresh_click(e):
        if state["df"] is None:
            return
        search_field.value = ""
        page_size_dropdown.value = DEFAULT_PAGE_SIZE
        state["filtered_df"] = state["df"]
        state["page_size"] = int(DEFAULT_PAGE_SIZE)
        state["page"] = 0

        # Reset hasil perbandingan Apriori/FP-Growth sebelumnya,
        # supaya user bisa klik "Jalankan Perbandingan" lagi dari kondisi bersih
        results_container.controls = []
        state["last_comparison"] = None
        export_button.visible = False
        export_status_text.value = ""

        # Reset juga hasil uji multi-support sebelumnya
        multi_support_field.value = "5,10,20"
        multi_results_container.controls = []
        state["last_multi_results"] = None

        render_page()

    search_button.on_click = apply_search
    prev_button.on_click = on_prev_click
    next_button.on_click = on_next_click
    refresh_button.on_click = on_refresh_click

    # Dipanggil saat tombol "Jalankan Perbandingan" diklik
    def on_run_click(e):
        df = state["df"]
        if df is None:
            return  # belum ada data yang diupload, tidak bisa jalan

        # Fitur #4: validasi angka DAN rentang 0-100 (lihat data_utils.parse_percent_field)
        min_support, support_error = data_utils.parse_percent_field(min_support_field.value, "Minimum Support")
        min_confidence, confidence_error = data_utils.parse_percent_field(min_confidence_field.value, "Minimum Confidence")
        error_message = support_error or confidence_error

        if error_message:
            results_container.controls = [
                ft.Text(error_message, color=ft.Colors.RED_400)
            ]
            page.update()
            return

        # Panggil fungsi utama dari algorithms.py untuk menjalankan
        # Apriori & FP-Growth sekaligus, lalu ambil hasilnya
        comparison_result = algorithms.compare_algorithms(
            df=df,
            name_col=state["name_col"],
            factor_columns=state["factor_columns"],
            min_support=min_support,
            min_confidence=min_confidence,
        )

        # Simpan hasil ini ke state supaya bisa dipakai fitur export nanti,
        # juga simpan parameter yang dipakai (untuk dicatat di file Excel)
        state["last_comparison"] = comparison_result
        state["last_min_support"] = min_support
        state["last_min_confidence"] = min_confidence
        export_button.visible = True

        # Tampilkan hasil kedua algoritma berdampingan dalam 2 kartu ringkasan.
        # Detail rules tidak lagi ditampilkan langsung di halaman, tapi lewat
        # tombol "Detail Rules" yang membuka modal (lihat ui_dialogs.py)
        results_container.controls = [
            ft.Row(
                [
                    ui_dialogs.build_result_card(
                        page, "Apriori", comparison_result["apriori"], ft.Colors.ORANGE_400,
                        other_result=comparison_result["fpgrowth"],
                    ),
                    ui_dialogs.build_result_card(
                        page, "FP-Growth", comparison_result["fpgrowth"], ft.Colors.CYAN_400,
                        other_result=comparison_result["apriori"],
                    ),
                ],
                spacing=16,
            ),
        ]
        page.update()

    run_button.on_click = on_run_click

    # Dipanggil saat tombol "Jalankan Uji Multi-Support" diklik
    def on_multi_run_click(e):
        df = state["df"]
        if df is None:
            return

        # Ambil daftar nilai support dari input, misal "5,10,20" -> [0.05, 0.1, 0.2]
        # Setiap nilai divalidasi satu per satu lewat data_utils.parse_percent_field
        # supaya ikut tervalidasi rentang 0-100 (bukan cuma dicek apakah berupa angka).
        raw_support_values = [v.strip() for v in multi_support_field.value.split(",") if v.strip() != ""]

        if not raw_support_values:
            multi_results_container.controls = [
                ft.Text("Isi minimal 1 nilai minimum support.", color=ft.Colors.RED_400)
            ]
            page.update()
            return

        support_values = []
        error_message = None
        for raw_value in raw_support_values:
            parsed_value, value_error = data_utils.parse_percent_field(raw_value, "Minimum Support")
            if value_error:
                error_message = value_error
                break
            support_values.append(parsed_value)

        if error_message is None:
            min_confidence, confidence_error = data_utils.parse_percent_field(min_confidence_field.value, "Minimum Confidence")
            error_message = confidence_error

        if error_message:
            multi_results_container.controls = [
                ft.Text(error_message, color=ft.Colors.RED_400)
            ]
            page.update()
            return

        multi_results = algorithms.compare_across_supports(
            df=df,
            name_col=state["name_col"],
            factor_columns=state["factor_columns"],
            support_values=support_values,
            min_confidence=min_confidence,
        )

        # Simpan hasil ini ke state supaya ikut disertakan saat export ke Excel
        state["last_multi_results"] = multi_results

        multi_results_container.controls = [
            ui_tables.build_multi_support_table(multi_results),
            ft.Row(
                [
                    ft.Button(
                        "Lihat Ringkasan Observasi",
                        icon=ft.Icons.INSIGHTS,
                        on_click=lambda e: ui_dialogs.open_observation_dialog(page, multi_results),
                    ),
                    ft.Button(
                        "Lihat Grafik Tren",
                        icon=ft.Icons.SHOW_CHART,
                        on_click=lambda e: ui_dialogs.open_trend_dialog(page, multi_results),
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
                spacing=12,
            ),
        ]
        page.update()

    multi_run_button.on_click = on_multi_run_click

    # ---------------------------------------------------------------
    # FILE PICKER
    # ---------------------------------------------------------------
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    # Dipanggil saat tombol "Export Hasil ke Excel" diklik.
    # Membuka dialog "Save As" bawaan sistem, lalu menyimpan seluruh hasil
    # (ringkasan, rules, dan hasil multi-support kalau ada) ke 1 file Excel.
    async def on_export_click(e):
        if state["last_comparison"] is None:
            return  # belum ada hasil "Jalankan Perbandingan" yang bisa diexport

        save_path = await file_picker.save_file(
            file_name="hasil_perbandingan_apriori_fpgrowth.xlsx",
            allowed_extensions=["xlsx"],
        )

        if not save_path:
            return  # user membatalkan dialog save

        try:
            algorithms.export_results_to_excel(
                file_path=save_path,
                comparison_result=state["last_comparison"],
                min_support=state["last_min_support"],
                min_confidence=state["last_min_confidence"],
                multi_results=state["last_multi_results"],
            )
            export_status_text.value = f"Berhasil disimpan ke: {save_path}"
            export_status_text.color = ft.Colors.GREEN_400
        except Exception as ex:
            export_status_text.value = f"Gagal export: {ex}"
            export_status_text.color = ft.Colors.RED_400

        page.update()

    export_button.on_click = on_export_click

    # Dipanggil saat tombol "Pilih File Excel" diklik: baca file, deteksi
    # kolom nama kapal (Fitur #5), validasi isi data (Fitur #2), lalu
    # tampilkan hasilnya di tabel preview.
    async def on_upload_click(e):
        files = await file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["xlsx", "xls"],
        )

        if not files:
            return

        file_path = files[0].path
        try:
            df = pd.read_excel(file_path)

            if "No" in df.columns:
                df = df.drop(columns=["No"])

            name_col = data_utils.detect_name_column(list(df.columns))
            factor_columns = [c for c in df.columns if c != name_col]

            state["df"] = df
            state["filtered_df"] = df
            state["name_col"] = name_col
            state["factor_columns"] = factor_columns
            state["page"] = 0
            state["page_size"] = int(DEFAULT_PAGE_SIZE)

            status_text.value = f"File berhasil dimuat: {files[0].name} ({len(df)} baris)"
            status_text.color = ft.Colors.GREEN_400

            # Validasi: pastikan kolom faktor cuma berisi 0/1 (bukan kosong/teks lain).
            # Ini cuma peringatan (tidak menghentikan proses), karena data yang tidak
            # sesuai tetap akan dianggap "0" oleh program — tapi user perlu tahu
            # kalau ada data yang mungkin salah ketik/kosong sebelum lanjut analisis.
            validation = algorithms.validate_transaction_data(df, name_col, factor_columns)
            if validation["is_valid"]:
                validation_banner.visible = False
            else:
                issues = validation["issues"]
                shown_issues = issues[:8]
                more_count = len(issues) - len(shown_issues)

                issue_lines = [ft.Text(f"• {msg}", size=12, color=ft.Colors.AMBER_200) for msg in shown_issues]
                if more_count > 0:
                    issue_lines.append(
                        ft.Text(f"...dan {more_count} masalah lainnya.", size=12, color=ft.Colors.AMBER_200, italic=True)
                    )

                validation_banner.content = ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER_400, size=18),
                                    ft.Text(
                                        f"Ditemukan {len(issues)} sel bermasalah di kolom faktor (kosong atau bukan 0/1). "
                                        f"Data ini tetap akan diproses (dianggap 0), tapi disarankan dicek ulang di Excel:",
                                        size=12,
                                        color=ft.Colors.AMBER_200,
                                    ),
                                ],
                                spacing=8,
                            ),
                            ft.Column(issue_lines, spacing=2),
                        ],
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.AMBER_900,
                    border_radius=10,
                    padding=14,
                    border=ft.Border.all(1, ft.Colors.AMBER_700),
                )
                validation_banner.visible = True

            search_field.value = ""
            page_size_dropdown.value = DEFAULT_PAGE_SIZE

            search_field.visible = True
            page_size_dropdown.visible = True
            search_button.visible = True
            prev_button.visible = True
            next_button.visible = True

            # Tampilkan juga kontrol parameter & tombol jalankan setelah data siap
            min_support_field.visible = True
            min_confidence_field.visible = True
            run_button.visible = True
            results_container.controls = []  # reset hasil lama kalau upload file baru

            # Tampilkan juga kontrol untuk fitur uji multi-support
            multi_support_field.visible = True
            multi_run_button.visible = True
            multi_results_container.controls = []

            render_page()

        except Exception as ex:
            status_text.value = f"Gagal membaca file: {ex}"
            status_text.color = ft.Colors.RED_400
            table_container.controls = []
            page.update()

    upload_button = ft.Button(
        "Pilih File Excel",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=on_upload_click,
    )

    # ---------------------------------------------------------------
    # LAYOUT
    # ---------------------------------------------------------------
    header_texts = ft.Column(
        [
            ft.Text("Perbandingan Kinerja Apriori vs FP-Growth", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("Preview & Eksplorasi Data Kapal", size=14, color=ft.Colors.GREY_400),
        ],
        spacing=2,
    )

    header_row = ft.Row(
        [header_texts, refresh_button],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    toolbar = ft.Row(
        [upload_button, status_text],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=16,
    )

    filter_bar = ft.Row(
        [search_field, page_size_dropdown, search_button],
        spacing=16,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    pagination_bar = ft.Row(
        [prev_button, page_label, next_button],
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
    )

    card = ft.Container(
        content=ft.Column(
            [
                filter_bar,
                ft.Divider(height=1, color=ft.Colors.GREY_800),
                table_container,
                pagination_bar,
            ],
            spacing=16,
        ),
        bgcolor=ft.Colors.GREY_900,
        padding=20,
        border_radius=14,
        border=ft.Border.all(1, ft.Colors.GREY_800),
        expand=True,
    )

    # Baris berisi input parameter algoritma & tombol jalankan
    params_row = ft.Row(
        [min_support_field, min_confidence_field, run_button],
        spacing=16,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Card khusus untuk parameter + hasil perbandingan algoritma
    comparison_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Parameter & Jalankan Perbandingan", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"Setiap algoritma dijalankan {algorithms.DEFAULT_N_RUNS}x secara berulang untuk nilai "
                    f"parameter yang sama, lalu dirata-ratakan agar pengukuran waktu lebih stabil (tidak "
                    f"terpengaruh noise satu kali percobaan). Proses mungkin perlu beberapa saat.",
                    size=12,
                    color=ft.Colors.GREY_400,
                ),
                params_row,
                results_container,
                ft.Row([export_button], alignment=ft.MainAxisAlignment.END),
                ft.Row([export_status_text], alignment=ft.MainAxisAlignment.END),
            ],
            spacing=16,
        ),
        bgcolor=ft.Colors.GREY_900,
        padding=20,
        border_radius=14,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

    # Baris berisi input daftar support & tombol jalankan uji multi-support
    multi_support_row = ft.Row(
        [multi_support_field, multi_run_button],
        spacing=16,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Card khusus untuk fitur uji beberapa nilai minimum support sekaligus
    multi_support_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Uji Beberapa Nilai Minimum Support Sekaligus", size=16, weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"Minimum Confidence mengikuti nilai di atas. Tiap nilai support juga diukur dari rata-rata "
                    f"{algorithms.DEFAULT_N_RUNS}x run, jadi semakin banyak nilai support yang diuji sekaligus, "
                    f"semakin lama prosesnya.",
                    size=12,
                    color=ft.Colors.GREY_400,
                ),
                multi_support_row,
                multi_results_container,
            ],
            spacing=16,
        ),
        bgcolor=ft.Colors.GREY_900,
        padding=20,
        border_radius=14,
        border=ft.Border.all(1, ft.Colors.GREY_800),
    )

    page.add(
        header_row,
        ft.Container(height=8),
        toolbar,
        ft.Container(height=12),
        validation_banner,
        ft.Container(height=16),
        card,
        ft.Container(height=16),
        comparison_card,
        ft.Container(height=16),
        multi_support_card,
    )


ft.run(main)