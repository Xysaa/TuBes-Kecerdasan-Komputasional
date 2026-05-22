"""
gui/main_window.py — Window Utama Aplikasi
===========================================
Window utama PyQt5 yang mengintegrasikan semua panel:
  - Panel kiri  : Input lokasi, parameter ACO & Fuzzy
  - Panel tengah: Visualisasi peta & rute
  - Panel kanan : Hasil optimasi, statistik, grafik konvergensi

  PIC:  Jefri Wahyu Fernando Sembiring

CHANGELOG:
  - FIX: Sambungkan sinyal location_clicked dari MapCanvas ke handler
  - FIX: Panel kiri & kanan bisa di-resize bebas via QSplitter
  - FIX: Tambah setCollapsible(False) agar panel tidak bisa di-collapse
  - ADD: _on_map_clicked() — handler klik peta → tambah baris ke tabel
"""

import sys
import json
import time

import pandas as pd

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QMenuBar, QMenu, QAction, QStatusBar,
    QMessageBox, QFileDialog, QProgressBar, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QPushButton, QFormLayout, QHeaderView,
    QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from gui.map_canvas import MapCanvas
from gui.result_panel import ResultPanel

from core.vrp_model import VRPProblem, DeliveryNode, Vehicle
from core.aco import ACOSolver
from core.fuzzy_evaluator import FuzzyEvaluator

from data.osm_handler import OSMHandler


class SolverThread(QThread):
    """
    Thread terpisah untuk menjalankan ACO agar GUI tidak freeze saat optimasi.
    """
    progress_updated = pyqtSignal(int, float)
    finished         = pyqtSignal(dict)
    error            = pyqtSignal(str)

    def __init__(self, problem, solver_params: dict):
        super().__init__()
        self.problem       = problem
        self.solver_params = solver_params
        self._stop_flag    = False

    def run(self):
        try:
            solver = ACOSolver(self.problem, **self.solver_params)

            def callback(iteration, best_distance):
                if self._stop_flag:
                    raise InterruptedError("Optimasi dihentikan oleh pengguna.")
                self.progress_updated.emit(iteration, best_distance)

            solution = solver.solve(callback=callback)
            self.finished.emit(solution)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._stop_flag = True


class InputPanel(QWidget):
    """
    Panel input di sisi kiri: lokasi pengiriman dan parameter algoritma.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── FIX: SizePolicy agar panel bisa di-resize bebas ──────────────────
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setMinimumWidth(200)

        self.layout = QVBoxLayout(self)
        self.tabs   = QTabWidget()

        # ── Tab 1: Lokasi ──────────────────────────────────────────────────────
        self.tab_loc    = QWidget()
        self.loc_layout = QVBoxLayout(self.tab_loc)

        self.loc_table = QTableWidget(0, 5)
        self.loc_table.setHorizontalHeaderLabels(
            ["Nama", "Lat", "Lon", "Berat (kg)", "Deadline (jam)"]
        )
        self.loc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.loc_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.btn_add_loc = QPushButton("Tambah Lokasi")
        self.btn_del_loc = QPushButton("Hapus Lokasi")

        self.loc_layout.addWidget(self.loc_table)
        self.loc_layout.addWidget(self.btn_add_loc)
        self.loc_layout.addWidget(self.btn_del_loc)

        self.btn_add_loc.clicked.connect(
            lambda: self.loc_table.insertRow(self.loc_table.rowCount())
        )
        self.btn_del_loc.clicked.connect(
            lambda: self.loc_table.removeRow(self.loc_table.currentRow())
        )

        # ── Tab 2: ACO ────────────────────────────────────────────────────────
        self.tab_aco    = QWidget()
        self.aco_layout = QFormLayout(self.tab_aco)

        self.spin_ants  = QSpinBox();       self.spin_ants.setRange(1, 200);     self.spin_ants.setValue(30)
        self.spin_iter  = QSpinBox();       self.spin_iter.setRange(1, 1000);    self.spin_iter.setValue(200)
        self.spin_alpha = QDoubleSpinBox(); self.spin_alpha.setRange(0.1, 10.0); self.spin_alpha.setValue(1.0)
        self.spin_beta  = QDoubleSpinBox(); self.spin_beta.setRange(0.1, 10.0);  self.spin_beta.setValue(3.0)
        self.spin_rho   = QDoubleSpinBox(); self.spin_rho.setRange(0.01, 0.99);  self.spin_rho.setValue(0.3)
        self.spin_q     = QDoubleSpinBox(); self.spin_q.setRange(1.0, 10000.0);  self.spin_q.setValue(100.0)

        self.aco_layout.addRow("Jumlah Semut:",     self.spin_ants)
        self.aco_layout.addRow("Jumlah Iterasi:",   self.spin_iter)
        self.aco_layout.addRow("Alpha (Feromon):",  self.spin_alpha)
        self.aco_layout.addRow("Beta (Heuristik):", self.spin_beta)
        self.aco_layout.addRow("Rho (Evaporasi):",  self.spin_rho)
        self.aco_layout.addRow("Q (Konstanta):",    self.spin_q)

        # ── Tab 3: Kendaraan ──────────────────────────────────────────────────
        self.tab_veh    = QWidget()
        self.veh_layout = QFormLayout(self.tab_veh)

        self.spin_n_veh = QSpinBox();       self.spin_n_veh.setRange(1, 50);     self.spin_n_veh.setValue(2)
        self.spin_cap   = QDoubleSpinBox(); self.spin_cap.setRange(1.0, 1000.0); self.spin_cap.setValue(50.0)

        self.veh_layout.addRow("Jumlah Kendaraan:", self.spin_n_veh)
        self.veh_layout.addRow("Kapasitas (kg):",   self.spin_cap)

        self.tabs.addTab(self.tab_loc, "Lokasi")
        self.tabs.addTab(self.tab_aco, "ACO")
        self.tabs.addTab(self.tab_veh, "Kendaraan")

        self.btn_load = QPushButton("Muat Sample Data")
        self.btn_run  = QPushButton("Jalankan Optimasi")

        self.btn_load.clicked.connect(self.load_sample_data)

        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.btn_load)
        self.layout.addWidget(self.btn_run)

    def get_locations(self) -> list:
        locations = []
        for row in range(self.loc_table.rowCount()):
            try:
                name     = self.loc_table.item(row, 0).text()
                lat      = float(self.loc_table.item(row, 1).text())
                lon      = float(self.loc_table.item(row, 2).text())
                weight   = float(self.loc_table.item(row, 3).text())
                deadline = float(self.loc_table.item(row, 4).text())
                locations.append({
                    "name": name, "lat": lat, "lon": lon,
                    "weight_kg": weight, "deadline_h": deadline
                })
            except (AttributeError, ValueError):
                continue
        return locations

    def get_aco_params(self) -> dict:
        return {
            "n_ants":       self.spin_ants.value(),
            "n_iterations": self.spin_iter.value(),
            "alpha":        self.spin_alpha.value(),
            "beta":         self.spin_beta.value(),
            "rho":          self.spin_rho.value(),
            "Q":            self.spin_q.value()
        }

    def get_vehicle_config(self) -> dict:
        return {
            "n_vehicles":  self.spin_n_veh.value(),
            "capacity_kg": self.spin_cap.value()
        }

    def load_sample_data(self):
        try:
            with open("data/sample_locations.json", "r") as f:
                data = json.load(f)

            self.loc_table.setRowCount(0)
            depot = data.get("depot", {})
            nodes = [depot] + data.get("delivery_nodes", [])

            for item in nodes:
                row_idx = self.loc_table.rowCount()
                self.loc_table.insertRow(row_idx)
                self.loc_table.setItem(row_idx, 0, QTableWidgetItem(str(item.get("name",       ""))))
                self.loc_table.setItem(row_idx, 1, QTableWidgetItem(str(item.get("lat",        0.0))))
                self.loc_table.setItem(row_idx, 2, QTableWidgetItem(str(item.get("lon",        0.0))))
                self.loc_table.setItem(row_idx, 3, QTableWidgetItem(str(item.get("weight_kg",  0.0))))
                self.loc_table.setItem(row_idx, 4, QTableWidgetItem(str(item.get("deadline_h", 0.0))))

            vehicles = data.get("vehicles", [])
            if vehicles:
                self.spin_n_veh.setValue(len(vehicles))
                self.spin_cap.setValue(vehicles[0].get("capacity_kg", 50.0))

            QMessageBox.information(self, "Info", "Sample data berhasil dimuat.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal memuat sample data:\n{e}")


class MainWindow(QMainWindow):
    """
    Class utama aplikasi yang menampung dan mengatur interaksi seluruh panel.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VRP Optimizer — ACO + Fuzzy Logic")
        self.setMinimumSize(1200, 700)

        self.solver_thread   = None
        self.current_problem = None
        self.start_time      = 0.0

        self._init_ui()
        self._init_menubar()
        self._init_statusbar()

    def _init_ui(self):
        """Menyiapkan tata letak aplikasi dengan QSplitter yang bisa di-resize."""

        # ── FIX: Splitter utama (horizontal: kiri | tengah | kanan) ──────────
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(6)          # handle lebih lebar → mudah di-drag
        self.splitter.setChildrenCollapsible(False)  # panel tidak bisa di-collapse

        self.input_panel  = InputPanel()
        self.map_canvas   = MapCanvas()
        self.result_panel = ResultPanel()

        # Beri SizePolicy agar map bisa mengembang maksimal
        self.map_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Beri SizePolicy agar result panel bisa di-resize
        self.result_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.result_panel.setMinimumWidth(200)

        self.splitter.addWidget(self.input_panel)
        self.splitter.addWidget(self.map_canvas)
        self.splitter.addWidget(self.result_panel)

        # Stretch factor: kiri=0, tengah=1 (mengembang), kanan=0
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)

        # Ukuran awal panel (bisa di-drag bebas setelahnya)
        self.splitter.setSizes([300, 600, 300])

        self.setCentralWidget(self.splitter)
        self.input_panel.btn_run.clicked.connect(self.run_optimization)

        # ── FIX: sambungkan sinyal klik peta ke handler penambah lokasi ───────
        self.map_canvas.location_clicked.connect(self._on_map_clicked)

    def _on_map_clicked(self, lat: float, lon: float):
        """
        Dipanggil otomatis ketika user klik pada peta.
        Menambahkan baris baru ke tabel lokasi dengan koordinat yang diklik.
        """
        table = self.input_panel.loc_table
        row   = table.rowCount()
        table.insertRow(row)

        # Nama otomatis: Lokasi-1, Lokasi-2, dst
        name = f"Lokasi-{row}"

        table.setItem(row, 0, QTableWidgetItem(name))
        table.setItem(row, 1, QTableWidgetItem(f"{lat:.6f}"))
        table.setItem(row, 2, QTableWidgetItem(f"{lon:.6f}"))
        table.setItem(row, 3, QTableWidgetItem("10.0"))   # default berat (kg)
        table.setItem(row, 4, QTableWidgetItem("8.0"))    # default deadline (jam)

        # Switch ke tab Lokasi agar user langsung melihat hasilnya
        self.input_panel.tabs.setCurrentIndex(0)

        self.status_label.setText(
            f"📍 Lokasi ditambahkan: {name}  ({lat:.5f}, {lon:.5f})"
        )

    def _init_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        load_action = QAction("Muat Data (JSON)", self)
        load_action.triggered.connect(self.load_data_from_file)
        file_menu.addAction(load_action)

        export_action = QAction("Ekspor Hasil (CSV)", self)
        export_action.triggered.connect(self.export_results)
        file_menu.addAction(export_action)

        exit_action = QAction("Keluar", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_menu   = menubar.addMenu("Tentang")
        about_action = QAction("Tentang Aplikasi", self)
        about_action.triggered.connect(
            lambda: QMessageBox.information(
                self, "Tentang",
                "VARCO — VRP Optimizer\nBerbasis ACO & Fuzzy Logic\n"
                "Kecerdasan Komputasional 2025/2026"
            )
        )
        about_menu.addAction(about_action)

    def _init_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.status_label = QLabel("Siap.")

        self.statusbar.addWidget(self.status_label)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def run_optimization(self):
        locs = self.input_panel.get_locations()
        if len(locs) < 2:
            QMessageBox.warning(self, "Peringatan",
                                "Minimal harus ada 2 lokasi (1 Depot, 1 Tujuan).")
            return

        aco_params = self.input_panel.get_aco_params()
        veh_config = self.input_panel.get_vehicle_config()

        depot_data = locs[0]
        depot = DeliveryNode(
            0, depot_data["name"], depot_data["lat"], depot_data["lon"],
            depot_data["weight_kg"], depot_data["deadline_h"]
        )

        nodes = [
            DeliveryNode(i, d["name"], d["lat"], d["lon"],
                         d["weight_kg"], d["deadline_h"])
            for i, d in enumerate(locs[1:], start=1)
        ]

        vehicles = [
            Vehicle(v_id, veh_config["capacity_kg"])
            for v_id in range(1, veh_config["n_vehicles"] + 1)
        ]

        self.current_problem = VRPProblem(depot, nodes, vehicles)

        try:
            self.status_label.setText("Memuat Map OSM dan menghitung jarak...")
            QApplication.processEvents()

            osm = OSMHandler()
            osm.load_graph()
            dist_matrix = osm.compute_distance_matrix(self.current_problem)
            self.current_problem.dist_matrix = dist_matrix

            self.status_label.setText("Mengevaluasi prioritas dengan Fuzzy Logic...")
            QApplication.processEvents()

            fuzzy = FuzzyEvaluator()
            fuzzy.evaluate_all(nodes, dist_matrix)

        except Exception as e:
            self.on_solver_error(f"Gagal saat inisialisasi Map/Fuzzy: {e}")
            return

        self.input_panel.btn_run.setEnabled(False)
        self.progress_bar.setMaximum(aco_params["n_iterations"])
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.start_time = time.time()

        self.solver_thread = SolverThread(self.current_problem, aco_params)
        self.solver_thread.progress_updated.connect(self.on_progress)
        self.solver_thread.finished.connect(self.on_solver_finished)
        self.solver_thread.error.connect(self.on_solver_error)
        self.solver_thread.start()

    def on_progress(self, iteration: int, best_distance: float):
        self.progress_bar.setValue(iteration)
        self.status_label.setText(
            f"Iterasi {iteration} — Jarak terbaik: {best_distance / 1000:.2f} km"
        )

    def on_solver_finished(self, solution: dict):
        elapsed_time = time.time() - self.start_time

        self.progress_bar.setVisible(False)
        self.input_panel.btn_run.setEnabled(True)
        self.status_label.setText(
            f"Selesai! Total jarak: {solution['distance'] / 1000:.2f} km"
        )

        self.map_canvas.plot_solution(
            solution,
            self.current_problem.nodes,
            self.current_problem.depot,
            self.current_problem
        )
        self.result_panel.update_results(solution, self.current_problem.nodes, elapsed_time)

    def on_solver_error(self, error_message: str):
        self.progress_bar.setVisible(False)
        self.input_panel.btn_run.setEnabled(True)
        self.status_label.setText("Terjadi kesalahan.")
        QMessageBox.critical(self, "Error Optimasi", error_message)

    def load_data_from_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Buka File Lokasi", "", "JSON Files (*.json)"
        )
        if filepath:
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)

                self.input_panel.loc_table.setRowCount(0)
                nodes = [data.get("depot", {})] + data.get("delivery_nodes", [])

                for item in nodes:
                    row_idx = self.input_panel.loc_table.rowCount()
                    self.input_panel.loc_table.insertRow(row_idx)
                    self.input_panel.loc_table.setItem(row_idx, 0, QTableWidgetItem(str(item.get("name",       ""))))
                    self.input_panel.loc_table.setItem(row_idx, 1, QTableWidgetItem(str(item.get("lat",        0.0))))
                    self.input_panel.loc_table.setItem(row_idx, 2, QTableWidgetItem(str(item.get("lon",        0.0))))
                    self.input_panel.loc_table.setItem(row_idx, 3, QTableWidgetItem(str(item.get("weight_kg",  0.0))))
                    self.input_panel.loc_table.setItem(row_idx, 4, QTableWidgetItem(str(item.get("deadline_h", 0.0))))

                QMessageBox.information(self, "Berhasil", "Data berhasil dimuat.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal membaca file:\n{e}")

    def export_results(self):
        if not hasattr(self.result_panel, "current_solution") or not self.result_panel.current_solution:
            QMessageBox.warning(self, "Peringatan",
                                "Belum ada hasil optimasi untuk diekspor.")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan Hasil", "hasil_optimasi.csv", "CSV Files (*.csv)"
        )
        if filepath:
            try:
                routes_data = []
                solution    = self.result_panel.current_solution
                all_nodes   = self.current_problem.get_all_nodes()

                for i, route in enumerate(solution["routes"]):
                    route_names = []
                    for idx in route:
                        if 0 <= idx < len(all_nodes):
                            route_names.append(all_nodes[idx].name)
                    routes_data.append({
                        "Kendaraan": i + 1,
                        "Rute":      " -> ".join(route_names)
                    })

                df = pd.DataFrame(routes_data)
                df.to_csv(filepath, index=False)

                QMessageBox.information(self, "Berhasil", "Hasil rute berhasil diekspor.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan file:\n{e}")