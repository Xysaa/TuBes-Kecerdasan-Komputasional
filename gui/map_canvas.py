"""
gui/map_canvas.py — Kanvas Visualisasi Peta & Rute
====================================================
Menampilkan visualisasi interaktif:
  - Titik-titik lokasi pengiriman di atas latar koordinat
  - Rute optimal per kendaraan (warna berbeda tiap kendaraan)
  - Animasi feromon bergerak (opsional, jika waktu cukup)
  - Tooltip nama & prioritas saat hover node

Menggunakan matplotlib embedded di PyQt5 via FigureCanvasQTAgg.

PIC: Anggota 4 (Data & Visualisasi)
Kolaborasi: Anggota 3 (embed ke main_window)
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolBar, QAction
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Warna untuk setiap kendaraan (maks 5 kendaraan)
VEHICLE_COLORS = ["#E74C3C", "#2ECC71", "#3498DB", "#F39C12", "#9B59B6"]


class MapCanvas(QWidget):
    """
    Widget kanvas untuk menampilkan peta dan rute pengiriman.
    """

    def __init__(self, parent=None):
        """
        TODO:
        - super().__init__(parent)
        - Buat self.figure = Figure(figsize=(8, 6))
        - Buat self.canvas = FigureCanvas(self.figure)
        - Buat self.ax = self.figure.add_subplot(111)
        - Buat NavigationToolbar untuk zoom/pan
        - Susun dalam QVBoxLayout: toolbar di atas, canvas di bawah
        - Panggil self._draw_empty_state()
        - Inisialisasi self.current_nodes = []
        - Inisialisasi self.current_solution = None
        """
        pass

    def _draw_empty_state(self):
        """
        Tampilkan placeholder saat belum ada data.

        TODO:
        - Bersihkan ax: self.ax.clear()
        - Tambahkan teks di tengah: "Tambahkan lokasi dan jalankan optimasi"
        - Style dengan warna abu-abu, font italic
        - self.canvas.draw()
        """
        pass

    def plot_nodes(self, nodes: list, depot):
        """
        Tampilkan semua titik lokasi di peta (sebelum ACO dijalankan).

        Parameter:
          nodes : list[DeliveryNode] — titik pengiriman
          depot : DeliveryNode — titik depot

        TODO:
        - Bersihkan ax
        - Plot depot dengan marker berbeda (misal: bintang ★, warna hitam, size besar)
        - Plot setiap delivery node dengan scatter:
            - Warna berdasarkan prioritas (merah=tinggi, hijau=rendah)
            - Annotate nama node di sebelah titik
        - Tambahkan colorbar untuk legenda prioritas
        - Set label sumbu: "Longitude" dan "Latitude"
        - Set judul: "Peta Lokasi Pengiriman"
        - self.canvas.draw()
        """
        pass

    def plot_solution(self, solution: dict, nodes: list, depot, problem):
        """
        Tampilkan rute optimal hasil ACO.

        Parameter:
          solution : dict {'routes': list[list[int]], 'distance': float}
          nodes    : list[DeliveryNode]
          depot    : DeliveryNode
          problem  : VRPProblem

        TODO:
        - Bersihkan ax
        - Panggil self.plot_nodes() sebagai base layer (tanpa draw dulu)
        - Untuk setiap rute (dengan index warna dari VEHICLE_COLORS):
            - Gambar garis dari depot → node1 → node2 → ... → depot
            - Gunakan ax.annotate() dengan arrowprops untuk arah panah
        - Tambahkan legend: nama kendaraan + warnanya
        - Tambahkan judul dengan total jarak
        - self.canvas.draw()
        - Simpan ke self.current_solution
        """
        pass

    def animate_iteration(self, pheromone_matrix, nodes: list, depot):
        """
        (Fitur opsional) Visualisasi intensitas feromon per iterasi.

        Parameter:
          pheromone_matrix: numpy array n×n feromon saat ini

        TODO:
        - Gambar garis antar semua pasang node
        - Ketebalan/opacity garis proporsional dengan nilai feromon
        - Update canvas tanpa clear seluruh gambar (blitting)
        - Hanya implementasikan jika waktu pengerjaan mencukupi
        """
        pass

    def clear(self):
        """
        TODO:
        - Reset ke empty state
        - Panggil self._draw_empty_state()
        """
        pass

    def save_figure(self, filepath: str):
        """
        Simpan visualisasi saat ini ke file gambar.

        TODO:
        - self.figure.savefig(filepath, dpi=150, bbox_inches='tight')
        """
        pass
