"""
gui/main_window.py — Window Utama Aplikasi
===========================================
Window utama PyQt5 yang mengintegrasikan semua panel:
  - Panel kiri  : Input lokasi, parameter ACO & Fuzzy
  - Panel tengah: Visualisasi peta & rute
  - Panel kanan : Hasil optimasi, statistik, grafik konvergensi

Layout utama menggunakan QSplitter agar user bisa resize panel.

PIC: Anggota 3 (GUI Developer)
Kolaborasi: Anggota 4 (embed map_canvas), Anggota 5 (review UX)
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QMenuBar, QMenu, QAction, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from gui.map_canvas import MapCanvas
from gui.result_panel import ResultPanel


class SolverThread(QThread):
    """
    Thread terpisah untuk menjalankan ACO agar GUI tidak freeze.

    Signals:
      progress_updated : (int iteration, float best_distance)
      finished         : (dict solution)
      error            : (str error_message)

    TODO:
    - Implementasi __init__(self, problem, solver_params)
    - Implementasi run(): jalankan ACO, emit signal progress & finished
    - Implementasi stop(): set flag untuk menghentikan solver
    """

    progress_updated = pyqtSignal(int, float)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, problem, solver_params: dict):
        """
        TODO:
        - super().__init__()
        - Simpan problem dan solver_params
        - Inisialisasi self._stop_flag = False
        """
        pass

    def run(self):
        """
        TODO:
        - Buat instance ACOSolver dengan problem dan solver_params
        - Definisikan callback yang emit progress_updated
        - Jalankan solver.solve(callback=callback)
        - Emit self.finished(solution)
        - Tangani exception: emit self.error(str(e))
        """
        pass

    def stop(self):
        """
        TODO:
        - Set self._stop_flag = True
        """
        pass


class InputPanel(QWidget):
    """
    Panel input di sisi kiri: lokasi pengiriman dan parameter algoritma.

    Berisi:
      - Tab 1: Manajemen lokasi (tambah/hapus node)
      - Tab 2: Parameter ACO (n_ants, n_iterations, alpha, beta, rho)
      - Tab 3: Parameter Fuzzy (bisa ditampilkan membership function)
      - Tombol "Muat Sample Data"
      - Tombol "Jalankan Optimasi"

    TODO:
    - Implementasi __init__ dengan semua widget
    - Implementasi get_locations() → list[dict] data lokasi dari form
    - Implementasi get_aco_params() → dict parameter ACO
    - Implementasi get_vehicle_config() → dict jumlah & kapasitas kendaraan
    - Implementasi load_sample_data() → isi form dari sample_locations.json
    """

    def __init__(self, parent=None):
        """
        TODO:
        - super().__init__(parent)
        - Buat layout: QVBoxLayout
        - Tambahkan QTabWidget dengan 3 tab (Lokasi, ACO, Kendaraan)
        - Di tab Lokasi: QTableWidget untuk daftar lokasi + tombol tambah/hapus
        - Di tab ACO: QDoubleSpinBox untuk setiap parameter
        - Di tab Kendaraan: QSpinBox jumlah kendaraan + QDoubleSpinBox kapasitas
        - Tombol "Load Sample" dan "Jalankan" di bawah
        """
        pass

    def get_locations(self) -> list:
        """
        TODO:
        - Baca semua baris dari QTableWidget lokasi
        - Return list of dict: [{name, lat, lon, weight_kg, deadline_h}, ...]
        """
        pass

    def get_aco_params(self) -> dict:
        """
        TODO:
        - Baca nilai dari semua QDoubleSpinBox parameter ACO
        - Return dict: {n_ants, n_iterations, alpha, beta, rho, Q}
        """
        pass

    def get_vehicle_config(self) -> dict:
        """
        TODO:
        - Return dict: {n_vehicles, capacity_kg}
        """
        pass

    def load_sample_data(self):
        """
        TODO:
        - Baca data/sample_locations.json
        - Isi QTableWidget dengan data lokasi dari JSON
        """
        pass


class MainWindow(QMainWindow):
    """
    Window utama aplikasi VRP-ACO-Fuzzy.
    """

    def __init__(self):
        """
        TODO:
        - super().__init__()
        - Set judul window: "VRP Optimizer — ACO + Fuzzy Logic"
        - Set ukuran minimal window: setMinimumSize(1200, 700)
        - Panggil self._init_ui()
        - Panggil self._init_menubar()
        - Panggil self._init_statusbar()
        - Inisialisasi self.solver_thread = None
        - Inisialisasi self.current_problem = None
        """
        pass

    def _init_ui(self):
        """
        Bangun layout utama dengan QSplitter.

        TODO:
        - Buat QSplitter(Qt.Horizontal) sebagai central widget
        - Tambahkan InputPanel di kiri (lebar ~300px)
        - Tambahkan MapCanvas di tengah (lebar ~600px)
        - Tambahkan ResultPanel di kanan (lebar ~300px)
        - Set splitter sebagai central widget
        - Hubungkan sinyal tombol "Jalankan" ke self.run_optimization()
        """
        pass

    def _init_menubar(self):
        """
        TODO:
        - Buat menu: File | Tentang
        - File > Muat Data (JSON) → self.load_data_from_file()
        - File > Ekspor Hasil (CSV) → self.export_results()
        - File > Keluar → self.close()
        - Tentang > Tentang Aplikasi → tampilkan dialog info
        """
        pass

    def _init_statusbar(self):
        """
        TODO:
        - Buat QStatusBar
        - Tambahkan QProgressBar (tersembunyi saat idle)
        - Tambahkan QLabel status teks
        """
        pass

    def run_optimization(self):
        """
        Dipanggil saat tombol "Jalankan Optimasi" ditekan.

        TODO:
        - Ambil data dari InputPanel: get_locations(), get_aco_params(), get_vehicle_config()
        - Validasi input: minimal 2 lokasi, semua field terisi
        - Bangun VRPProblem dari data input
        - Muat graf OSM (atau dari cache)
        - Jalankan FuzzyEvaluator untuk semua node
        - Hitung dist_matrix via OSMHandler
        - Buat SolverThread dan jalankan
        - Hubungkan sinyal: progress_updated → self.on_progress()
        - Hubungkan sinyal: finished → self.on_solver_finished()
        - Hubungkan sinyal: error → self.on_solver_error()
        - Tampilkan progress bar, disable tombol Jalankan
        """
        pass

    def on_progress(self, iteration: int, best_distance: float):
        """
        Dipanggil setiap iterasi ACO selesai.

        TODO:
        - Update progress bar berdasarkan iteration / n_iterations * 100
        - Update status bar: "Iterasi X — Jarak terbaik: Y.Y km"
        """
        pass

    def on_solver_finished(self, solution: dict):
        """
        Dipanggil saat ACO selesai menemukan solusi.

        TODO:
        - Sembunyikan progress bar
        - Enable tombol Jalankan
        - Kirim solution ke MapCanvas untuk visualisasi rute
        - Kirim solution ke ResultPanel untuk tampil statistik
        - Update status bar: "Selesai! Total jarak: X.X km"
        """
        pass

    def on_solver_error(self, error_message: str):
        """
        TODO:
        - Sembunyikan progress bar
        - Enable tombol Jalankan
        - Tampilkan QMessageBox.critical() dengan pesan error
        """
        pass

    def load_data_from_file(self):
        """
        TODO:
        - Buka QFileDialog untuk memilih file JSON
        - Baca dan parse file JSON
        - Isi InputPanel dengan data dari file
        """
        pass

    def export_results(self):
        """
        TODO:
        - Jika belum ada solusi, tampilkan pesan peringatan
        - Buka QFileDialog untuk memilih lokasi simpan CSV
        - Tulis rute, jarak, dan prioritas ke file CSV menggunakan pandas
        """
        pass
