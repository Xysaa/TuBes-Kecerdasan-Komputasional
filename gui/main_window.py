"""
gui/main_window.py — Window Utama Aplikasi
===========================================
Window utama PyQt5 yang mengintegrasikan semua panel:
  - Panel kiri  : Input lokasi, parameter ACO & Fuzzy
  - Panel tengah: Visualisasi peta & rute
  - Panel kanan : Hasil optimasi, statistik, grafik konvergensi

  PIC:  Jefri Wahyu Fernando Sembiring
"""

# Import modul bawaan Python
import sys
import json
import time

# Import pandas untuk export data ke bentuk CSV
import pandas as pd

# Import komponen-komponen antarmuka (GUI) dari PyQt5
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QMenuBar, QMenu, QAction, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QPushButton, QFormLayout, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

# Import panel dan kanvas custom yang sudah dibuat di file lain
from gui.map_canvas import MapCanvas
from gui.result_panel import ResultPanel

# Import modul inti (algoritma dan model data)
from core.vrp_model import VRPProblem, DeliveryNode, Vehicle
from core.aco import ACOSolver
from core.fuzzy_evaluator import FuzzyEvaluator

# Import modul untuk menangani data OpenStreetMap
from data.osm_handler import OSMHandler


class SolverThread(QThread):
    """
    Thread terpisah untuk menjalankan ACO agar GUI tidak freeze (lag) saat proses optimasi berjalan.
    """
    
    # Mendefinisikan sinyal yang akan dikirim dari thread ini ke GUI utama
    progress_updated = pyqtSignal(int, float) # Mengirim iterasi ke-berapa dan jarak terbaik sementara
    finished = pyqtSignal(dict)               # Mengirim hasil akhir solusi dalam bentuk dictionary
    error = pyqtSignal(str)                   # Mengirim pesan error jika terjadi kegagalan

    def __init__(self, problem, solver_params: dict):
        super().__init__()
        self.problem = problem                # Menyimpan objek VRPProblem (data lokasi & kendaraan)
        self.solver_params = solver_params    # Menyimpan parameter algoritma ACO
        self._stop_flag = False               # Flag penanda jika proses ingin dihentikan paksa

    def run(self):
        """Metode yang dijalankan saat thread dimulai (thread.start())."""
        try:
            # Menginisialisasi solver ACO dengan problem dan parameter yang ada
            solver = ACOSolver(self.problem, **self.solver_params)
            
            # Fungsi callback ini akan dipanggil oleh ACOSolver setiap kali satu iterasi selesai
            def callback(iteration, best_distance):
                # Jika tombol stop ditekan (meski belum diimplementasi di UI), hentikan proses
                if self._stop_flag:
                    raise InterruptedError("Optimasi dihentikan oleh pengguna.")
                # Kirim sinyal ke GUI utama untuk update Progress Bar
                self.progress_updated.emit(iteration, best_distance)
                
            # Jalankan proses optimasi
            solution = solver.solve(callback=callback)
            
            # Jika selesai tanpa error, kirim sinyal 'finished' beserta data solusinya
            self.finished.emit(solution)
            
        except Exception as e:
            # Jika terjadi error selama proses berjalan (misal masalah matriks dll), kirim sinyal error
            self.error.emit(str(e))

    def stop(self):
        """Metode untuk menghentikan thread di tengah jalan."""
        self._stop_flag = True


class InputPanel(QWidget):
    """
    Panel input di sisi kiri: Mengatur lokasi pengiriman dan mengubah parameter algoritma.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self) # Layout utama panel kiri (vertikal)
        self.tabs = QTabWidget()        # Menggunakan tab untuk merapikan input

        # ==========================================
        # TAB 1: Pengaturan Lokasi
        # ==========================================
        self.tab_loc = QWidget()
        self.loc_layout = QVBoxLayout(self.tab_loc)
        
        # Membuat tabel input untuk lokasi
        self.loc_table = QTableWidget(0, 5) # 0 baris awal, 5 kolom
        self.loc_table.setHorizontalHeaderLabels(["Nama", "Lat", "Lon", "Berat (kg)", "Deadline (jam)"])
        self.loc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Kolom menyesuaikan lebar tabel
        
        # Tombol aksi untuk tabel lokasi
        self.btn_add_loc = QPushButton("Tambah Lokasi")
        self.btn_del_loc = QPushButton("Hapus Lokasi")
        
        # Menambahkan widget ke dalam layout tab lokasi
        self.loc_layout.addWidget(self.loc_table)
        self.loc_layout.addWidget(self.btn_add_loc)
        self.loc_layout.addWidget(self.btn_del_loc)
        
        # Menghubungkan fungsi klik ke tombol
        self.btn_add_loc.clicked.connect(lambda: self.loc_table.insertRow(self.loc_table.rowCount()))
        self.btn_del_loc.clicked.connect(lambda: self.loc_table.removeRow(self.loc_table.currentRow()))

        # ==========================================
        # TAB 2: Parameter ACO
        # ==========================================
        self.tab_aco = QWidget()
        self.aco_layout = QFormLayout(self.tab_aco) # FormLayout agar rapi (Label : Input)
        
        # Membuat widget input angka untuk parameter ACO beserta batas-batas nilainya
        self.spin_ants = QSpinBox(); self.spin_ants.setRange(1, 200); self.spin_ants.setValue(30)
        self.spin_iter = QSpinBox(); self.spin_iter.setRange(1, 1000); self.spin_iter.setValue(200)
        self.spin_alpha = QDoubleSpinBox(); self.spin_alpha.setRange(0.1, 10.0); self.spin_alpha.setValue(1.0)
        self.spin_beta = QDoubleSpinBox(); self.spin_beta.setRange(0.1, 10.0); self.spin_beta.setValue(3.0)
        self.spin_rho = QDoubleSpinBox(); self.spin_rho.setRange(0.01, 0.99); self.spin_rho.setValue(0.3)
        self.spin_q = QDoubleSpinBox(); self.spin_q.setRange(1.0, 10000.0); self.spin_q.setValue(100.0)
        
        # Menambahkan baris input ke form layout ACO
        self.aco_layout.addRow("Jumlah Semut:", self.spin_ants)
        self.aco_layout.addRow("Jumlah Iterasi:", self.spin_iter)
        self.aco_layout.addRow("Alpha (Feromon):", self.spin_alpha)
        self.aco_layout.addRow("Beta (Heuristik):", self.spin_beta)
        self.aco_layout.addRow("Rho (Evaporasi):", self.spin_rho)
        self.aco_layout.addRow("Q (Konstanta):", self.spin_q)

        # ==========================================
        # TAB 3: Parameter Kendaraan
        # ==========================================
        self.tab_veh = QWidget()
        self.veh_layout = QFormLayout(self.tab_veh)
        
        # Input pengaturan kendaraan
        self.spin_n_veh = QSpinBox(); self.spin_n_veh.setRange(1, 50); self.spin_n_veh.setValue(2)
        self.spin_cap = QDoubleSpinBox(); self.spin_cap.setRange(1.0, 1000.0); self.spin_cap.setValue(50.0)
        
        # Menambahkan baris input ke form layout kendaraan
        self.veh_layout.addRow("Jumlah Kendaraan:", self.spin_n_veh)
        self.veh_layout.addRow("Kapasitas (kg):", self.spin_cap)

        # Memasukkan semua tab yang sudah dibuat ke dalam wadah tab utama
        self.tabs.addTab(self.tab_loc, "Lokasi")
        self.tabs.addTab(self.tab_aco, "ACO")
        self.tabs.addTab(self.tab_veh, "Kendaraan")

        # Tombol aksi utama di bagian bawah panel kiri
        self.btn_load = QPushButton("Muat Sample Data")
        self.btn_run = QPushButton("Jalankan Optimasi")
        
        # Hubungkan tombol load dengan fungsinya
        self.btn_load.clicked.connect(self.load_sample_data)

        # Menyusun semua komponen (Tab dan Tombol) ke dalam layout kiri
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.btn_load)
        self.layout.addWidget(self.btn_run)

    def get_locations(self) -> list:
        """Mengambil data dari QTableWidget lokasi dan mengembalikannya sebagai list of dictionaries."""
        locations = []
        for row in range(self.loc_table.rowCount()):
            try:
                # Mengambil teks dari setiap kolom pada baris saat ini dan di-convert ke tipe data yang sesuai
                name = self.loc_table.item(row, 0).text()
                lat = float(self.loc_table.item(row, 1).text())
                lon = float(self.loc_table.item(row, 2).text())
                weight = float(self.loc_table.item(row, 3).text())
                deadline = float(self.loc_table.item(row, 4).text())
                
                # Memasukkan data sebagai dictionary
                locations.append({"name": name, "lat": lat, "lon": lon, "weight_kg": weight, "deadline_h": deadline})
            except (AttributeError, ValueError):
                # Abaikan baris jika ada sel yang kosong atau tipe datanya salah
                continue
        return locations

    def get_aco_params(self) -> dict:
        """Mengambil nilai parameter ACO yang dimasukkan oleh user dari GUI."""
        return {
            "n_ants": self.spin_ants.value(),
            "n_iterations": self.spin_iter.value(),
            "alpha": self.spin_alpha.value(),
            "beta": self.spin_beta.value(),
            "rho": self.spin_rho.value(),
            "Q": self.spin_q.value()
        }

    def get_vehicle_config(self) -> dict:
        """Mengambil pengaturan armada kendaraan dari GUI."""
        return {
            "n_vehicles": self.spin_n_veh.value(),
            "capacity_kg": self.spin_cap.value()
        }

    def load_sample_data(self):
        """Memuat dataset sample dari file JSON dan mengisi form otomatis."""
        try:
            # Membuka dan membaca file JSON
            with open("data/sample_locations.json", "r") as f:
                data = json.load(f)
            
            # Bersihkan tabel lokasi jika sebelumnya ada isinya
            self.loc_table.setRowCount(0)
            
            # Gabungkan depot (baris pertama) dengan lokasi pengiriman lainnya
            depot = data.get("depot", {})
            nodes = [depot] + data.get("delivery_nodes", [])
            
            # Iterasi node dan masukkan ke dalam tabel
            for item in nodes:
                row_idx = self.loc_table.rowCount()
                self.loc_table.insertRow(row_idx)
                
                # Mengisi sel (baris, kolom) dengan data JSON
                self.loc_table.setItem(row_idx, 0, QTableWidgetItem(str(item.get("name", ""))))
                self.loc_table.setItem(row_idx, 1, QTableWidgetItem(str(item.get("lat", 0.0))))
                self.loc_table.setItem(row_idx, 2, QTableWidgetItem(str(item.get("lon", 0.0))))
                self.loc_table.setItem(row_idx, 3, QTableWidgetItem(str(item.get("weight_kg", 0.0))))
                self.loc_table.setItem(row_idx, 4, QTableWidgetItem(str(item.get("deadline_h", 0.0))))
                
            # Jika ada pengaturan kendaraan di JSON, update juga spinbox kendaraan
            vehicles = data.get("vehicles", [])
            if vehicles:
                self.spin_n_veh.setValue(len(vehicles))
                self.spin_cap.setValue(vehicles[0].get("capacity_kg", 50.0))
                
            # Menampilkan pesan sukses
            QMessageBox.information(self, "Info", "Sample data berhasil dimuat.")
        except Exception as e:
            # Menampilkan dialog error jika pembacaan file gagal
            QMessageBox.critical(self, "Error", f"Gagal memuat sample data:\n{e}")


class MainWindow(QMainWindow):
    """
    Class utama aplikasi yang menampung dan mengatur interaksi seluruh panel.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VRP Optimizer — ACO + Fuzzy Logic")
        self.setMinimumSize(1200, 700) # Ukuran minimum window agar UI tidak berantakan
        
        # Inisialisasi variabel state untuk menampung objek worker dan data
        self.solver_thread = None
        self.current_problem = None
        self.start_time = 0.0
        
        # Panggil fungsi-fungsi untuk membangun antarmuka UI
        self._init_ui()
        self._init_menubar()
        self._init_statusbar()

    def _init_ui(self):
        """Menyiapkan struktur tata letak aplikasi menggunakan Splitter."""
        self.splitter = QSplitter(Qt.Horizontal) # Splitter memungkinkan panel dapat digeser/di-resize oleh user
        
        # Menginisialisasi komponen panel (Kiri, Tengah, Kanan)
        self.input_panel = InputPanel()
        self.map_canvas = MapCanvas()
        self.result_panel = ResultPanel()
        
        # Memasukkan komponen ke dalam splitter secara berurutan
        self.splitter.addWidget(self.input_panel)
        self.splitter.addWidget(self.map_canvas)
        self.splitter.addWidget(self.result_panel)
        
        # Set rasio lebar awal panel: 300px (Kiri), 600px (Tengah), 300px (Kanan)
        self.splitter.setSizes([300, 600, 300])
        
        # Jadikan splitter sebagai widget di tengah (pusat) pada QMainWindow
        self.setCentralWidget(self.splitter)
        
        # Hubungkan tombol "Jalankan Optimasi" dari InputPanel ke method run_optimization
        self.input_panel.btn_run.clicked.connect(self.run_optimization)

    def _init_menubar(self):
        """Menyiapkan Menu Bar di atas (File, Tentang, dll)."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        # Aksi: Muat Data
        load_action = QAction("Muat Data (JSON)", self)
        load_action.triggered.connect(self.load_data_from_file)
        file_menu.addAction(load_action)
        
        # Aksi: Ekspor Hasil
        export_action = QAction("Ekspor Hasil (CSV)", self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)
        
        # Aksi: Keluar
        exit_action = QAction("Keluar", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Aksi: Tentang
        about_menu = menubar.addMenu("Tentang")
        about_action = QAction("Tentang Aplikasi", self)
        about_action.triggered.connect(lambda: QMessageBox.information(self, "Tentang", "VRP Optimizer\nBerbasis ACO & Fuzzy Logic."))
        about_menu.addAction(about_action)

    def _init_statusbar(self):
        """Menyiapkan Status Bar di bagian paling bawah aplikasi."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        # Progress bar (Awalnya disembunyikan karena belum jalan)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Label teks status
        self.status_label = QLabel("Siap.")
        
        # Memasukkan komponen ke status bar
        self.statusbar.addWidget(self.status_label)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def run_optimization(self):
        """Method utama yang mengeksekusi proses ketika tombol 'Jalankan Optimasi' ditekan."""
        # 1. Mengambil data mentah dari GUI
        locs = self.input_panel.get_locations()
        if len(locs) < 2:
            QMessageBox.warning(self, "Peringatan", "Minimal harus ada 2 lokasi (1 Depot, 1 Tujuan).")
            return
            
        aco_params = self.input_panel.get_aco_params()
        veh_config = self.input_panel.get_vehicle_config()
        
        # 2. Parsing data GUI menjadi Object Model (DeliveryNode & Vehicle)
        # Asumsikan baris 0 adalah depot/pusat
        depot_data = locs[0]
        depot = DeliveryNode(0, depot_data["name"], depot_data["lat"], depot_data["lon"], depot_data["weight_kg"], depot_data["deadline_h"])
        
        # Iterasi dari index 1 sampai akhir untuk titik pengiriman biasa
        nodes = []
        for i, data in enumerate(locs[1:], start=1):
            nodes.append(DeliveryNode(i, data["name"], data["lat"], data["lon"], data["weight_kg"], data["deadline_h"]))
            
        # Membuat list instance kendaraan
        vehicles = [Vehicle(v_id, veh_config["capacity_kg"]) for v_id in range(1, veh_config["n_vehicles"] + 1)]
        
        # Membentuk objek Root VRPProblem
        self.current_problem = VRPProblem(depot, nodes, vehicles)
        
        try:
            # 3. Download/Load Peta & Evaluasi Fuzzy Logic sebelum ACO berjalan
            self.status_label.setText("Memuat Map OSM dan menghitung jarak...")
            QApplication.processEvents() # Memaksa GUI memperbarui teks (agar tidak nge-freeze sementara)
            
            # Instansiasi Map OSMHandler dan menghitung matriks jarak
            osm = OSMHandler()
            osm.load_graph()
            dist_matrix = osm.compute_distance_matrix(self.current_problem)
            self.current_problem.dist_matrix = dist_matrix
            
            self.status_label.setText("Mengevaluasi prioritas dengan Fuzzy Logic...")
            QApplication.processEvents()
            
            # Hitung skor evaluasi fuzzy tiap node
            fuzzy = FuzzyEvaluator()
            fuzzy.evaluate_all(nodes, dist_matrix)
            
        except Exception as e:
            # Menggagalkan optimasi bila koneksi map putus dsb.
            self.on_solver_error(f"Gagal saat inisialisasi Map/Fuzzy: {e}")
            return
            
        # 4. Siapkan Antarmuka (UI) untuk loading progress
        self.input_panel.btn_run.setEnabled(False) # Nonaktifkan tombol run agar tidak di-spam click
        self.progress_bar.setMaximum(aco_params["n_iterations"]) # Max bar sesuai iterasi
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.start_time = time.time() # Mulai catat waktu eksekusi
        
        # 5. Jalankan algoritma ACO di Thread terpisah (Multithreading)
        self.solver_thread = SolverThread(self.current_problem, aco_params)
        
        # Hubungkan sinyal dari thread ke fungsi-fungsi penanganan (Event Driven)
        self.solver_thread.progress_updated.connect(self.on_progress)
        self.solver_thread.finished.connect(self.on_solver_finished)
        self.solver_thread.error.connect(self.on_solver_error)
        
        # Eksekusi!
        self.solver_thread.start()

    def on_progress(self, iteration: int, best_distance: float):
        """Method yang dipanggil secara berkala setiap iterasi selesai oleh solver thread."""
        self.progress_bar.setValue(iteration) # Update progress bar warna hijau
        self.status_label.setText(f"Iterasi {iteration} — Jarak terbaik: {best_distance / 1000:.2f} km")

    def on_solver_finished(self, solution: dict):
        """Method yang dipanggil saat algoritma optimasi telah selesai mengeksekusi semua iterasi."""
        elapsed_time = time.time() - self.start_time
        
        # Mengembalikan kondisi UI seperti semula (siap di-klik lagi)
        self.progress_bar.setVisible(False)
        self.input_panel.btn_run.setEnabled(True)
        self.status_label.setText(f"Selesai! Total jarak: {solution['distance'] / 1000:.2f} km")
        
        # Kirim data ke Panel Visual Map dan Panel Statistik untuk dirender
        self.map_canvas.plot_solution(solution, self.current_problem.nodes, self.current_problem.depot, self.current_problem)
        self.result_panel.update_results(solution, self.current_problem.nodes, elapsed_time)

    def on_solver_error(self, error_message: str):
        """Menangani jika ada logic di dalam algoritmanya yang crash."""
        self.progress_bar.setVisible(False)
        self.input_panel.btn_run.setEnabled(True)
        self.status_label.setText("Terjadi kesalahan.")
        QMessageBox.critical(self, "Error Optimasi", error_message)

    def load_data_from_file(self):
        """Fitur untuk mengimpor file JSON kustom dari File Explorer OS."""
        # Membuka dialog pemilih file
        filepath, _ = QFileDialog.getOpenFileName(self, "Buka File Lokasi", "", "JSON Files (*.json)")
        if filepath:
            try:
                # Proses mapping file sama seperti pada sample data
                with open(filepath, "r") as f:
                    data = json.load(f)
                
                self.input_panel.loc_table.setRowCount(0)
                nodes = [data.get("depot", {})] + data.get("delivery_nodes", [])
                
                for item in nodes:
                    row_idx = self.input_panel.loc_table.rowCount()
                    self.input_panel.loc_table.insertRow(row_idx)
                    self.input_panel.loc_table.setItem(row_idx, 0, QTableWidgetItem(str(item.get("name", ""))))
                    self.input_panel.loc_table.setItem(row_idx, 1, QTableWidgetItem(str(item.get("lat", 0.0))))
                    self.input_panel.loc_table.setItem(row_idx, 2, QTableWidgetItem(str(item.get("lon", 0.0))))
                    self.input_panel.loc_table.setItem(row_idx, 3, QTableWidgetItem(str(item.get("weight_kg", 0.0))))
                    self.input_panel.loc_table.setItem(row_idx, 4, QTableWidgetItem(str(item.get("deadline_h", 0.0))))
                
                QMessageBox.information(self, "Berhasil", "Data berhasil dimuat.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal membaca file:\n{e}")

    def export_results(self):
        """Fitur untuk mengekspor (download) hasil urutan rute ke dalam format Excel/CSV."""
        # Cek jika belum ada hasil optimasi yang berjalan
        if not hasattr(self.result_panel, "current_solution") or not self.result_panel.current_solution:
            QMessageBox.warning(self, "Peringatan", "Belum ada hasil optimasi untuk diekspor.")
            return
            
        # Membuka dialog untuk menyimpan file CSV
        filepath, _ = QFileDialog.getSaveFileName(self, "Simpan Hasil", "hasil_optimasi.csv", "CSV Files (*.csv)")
        if filepath:
            try:
                routes_data = []
                solution = self.result_panel.current_solution
                all_nodes = [self.current_problem.depot] + self.current_problem.nodes
                
                # Mengubah index/ID node hasil rute menjadi string rute bersambung (contoh: Depot -> A -> B)
                for i, route in enumerate(solution["routes"]):
                    route_names = [all_nodes[node_id].name for node_id in route]
                    routes_data.append({
                        "Kendaraan": i + 1,
                        "Rute": " -> ".join(route_names)
                    })
                
                # Gunakan pandas untuk konversi List of Dict menjadi format CSV
                df = pd.DataFrame(routes_data)
                df.to_csv(filepath, index=False)
                
                QMessageBox.information(self, "Berhasil", "Hasil rute berhasil diekspor.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan file:\n{e}")