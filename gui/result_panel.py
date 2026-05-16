"""
gui/result_panel.py — Panel Hasil & Statistik
===============================================
Menampilkan hasil optimasi setelah ACO selesai:
  - Ringkasan: total jarak, waktu komputasi, jumlah kendaraan aktif
  - Tabel rute per kendaraan (urutan node, jarak per rute)
  - Tabel prioritas Fuzzy setiap node
  - Grafik konvergensi: best distance vs iterasi

PIC: Anggota 4 (Data & Visualisasi)
Kolaborasi: Anggota 3 (layout & integrasi)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QLabel, QGroupBox, QGridLayout,
    QPushButton, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SummaryCard(QWidget):
    """
    Widget kartu ringkasan satu metrik (label + nilai besar).

    Contoh tampilan:
      ┌─────────────────┐
      │  Total Jarak    │
      │   24.7 km       │
      └─────────────────┘

    TODO:
    - Implementasi __init__(title, value="—", unit="")
    - Implementasi update_value(value, unit) untuk refresh angka
    """

    def __init__(self, title: str, value: str = "—", unit: str = ""):
        """
        TODO:
        - super().__init__()
        - Buat QGroupBox dengan title
        - Tambahkan QLabel untuk nilai (font besar, bold, warna aksen)
        - Tambahkan QLabel untuk unit (font kecil, abu-abu)
        """
        pass

    def update_value(self, value: str, unit: str = ""):
        """
        TODO:
        - Update teks QLabel nilai dan unit
        """
        pass


class ResultPanel(QWidget):
    """
    Panel lengkap yang menampilkan semua hasil optimasi.
    """

    def __init__(self, parent=None):
        """
        TODO:
        - super().__init__(parent)
        - Buat QVBoxLayout
        - Tambahkan judul "Hasil Optimasi" (QLabel, bold)
        - Buat baris kartu ringkasan (SummaryCard):
            - Total Jarak (km)
            - Waktu Komputasi (detik)
            - Kendaraan Aktif
        - Buat QTabWidget dengan 3 tab:
            Tab 1: "Rute" → QTableWidget
            Tab 2: "Prioritas Paket" → QTableWidget
            Tab 3: "Konvergensi" → grafik matplotlib
        - Tambahkan QPushButton "Ekspor CSV" di bawah
        - Inisialisasi self.current_solution = None
        """
        pass

    def _build_route_table(self) -> QTableWidget:
        """
        Buat QTableWidget untuk menampilkan rute.

        Kolom: No | Kendaraan | Urutan Rute | Jarak (km) | Muatan (kg)

        TODO:
        - Buat QTableWidget dengan 5 kolom
        - Set header kolom
        - Set horizontal header resize mode ke Stretch
        - Set selection behavior ke SelectRows
        - Return widget
        """
        pass

    def _build_priority_table(self) -> QTableWidget:
        """
        Buat QTableWidget untuk menampilkan prioritas Fuzzy setiap node.

        Kolom: No | Nama Lokasi | Deadline (jam) | Berat (kg) | Prioritas | Label

        TODO:
        - Buat QTableWidget dengan 6 kolom
        - Set header kolom
        - Return widget
        """
        pass

    def _build_convergence_chart(self) -> QWidget:
        """
        Buat grafik konvergensi menggunakan matplotlib.

        TODO:
        - Buat Figure dan FigureCanvas
        - Tambahkan subplot untuk plot garis
        - Set label sumbu: "Iterasi" (X) dan "Jarak Terbaik (m)" (Y)
        - Set judul: "Grafik Konvergensi ACO"
        - Return FigureCanvas (bukan Figure)
        """
        pass

    def update_results(self, solution: dict, nodes: list, elapsed_time: float):
        """
        Update seluruh panel dengan data hasil optimasi baru.

        Parameter:
          solution     : dict dari ACOSolver.solve()
          nodes        : list[DeliveryNode] dengan priority sudah terisi
          elapsed_time : float waktu komputasi dalam detik

        TODO:
        - Update kartu ringkasan (total jarak, waktu, jumlah kendaraan aktif)
        - Panggil self._fill_route_table(solution)
        - Panggil self._fill_priority_table(nodes)
        - Panggil self._plot_convergence(solution['history'])
        - Simpan ke self.current_solution
        """
        pass

    def _fill_route_table(self, solution: dict):
        """
        Isi tabel rute dengan data solusi.

        TODO:
        - Bersihkan tabel (setRowCount(0))
        - Untuk setiap kendaraan dan rutenya:
            - Tambahkan baris baru
            - Isi kolom: nomor, ID kendaraan, rute sebagai string "Depot → A → B → Depot",
              jarak rute, total muatan
            - Beri warna baris sesuai VEHICLE_COLORS
        """
        pass

    def _fill_priority_table(self, nodes: list):
        """
        Isi tabel prioritas Fuzzy.

        TODO:
        - Bersihkan tabel
        - Untuk setiap node:
            - Tambahkan baris: no, nama, deadline_h, weight_kg, priority (2 desimal), label
            - Warnai sel "Label" sesuai tingkat prioritas:
                Tinggi → merah muda (#FFCCCC)
                Sedang → kuning muda (#FFFACC)
                Rendah → hijau muda (#CCFFCC)
        """
        pass

    def _plot_convergence(self, history: list):
        """
        Plot grafik konvergensi (best distance per iterasi).

        TODO:
        - Bersihkan ax
        - Plot history sebagai garis biru
        - Tambahkan shaded area di bawah kurva (fill_between, alpha=0.2)
        - Tandai titik minimum dengan marker merah
        - Tambahkan annotasi nilai minimum
        - canvas.draw()
        """
        pass

    def clear(self):
        """
        TODO:
        - Reset semua kartu ringkasan ke "—"
        - Bersihkan kedua tabel
        - Bersihkan grafik konvergensi
        - Set self.current_solution = None
        """
        pass
