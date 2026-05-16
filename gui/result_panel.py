"""
gui/result_panel.py — Panel Hasil & Statistik
===============================================
Menampilkan hasil optimasi setelah ACO selesai:
  - Ringkasan: total jarak, waktu komputasi, jumlah kendaraan aktif
  - Tabel rute per kendaraan (urutan node, jarak per rute)
  - Tabel prioritas Fuzzy setiap node
  - Grafik konvergensi: best distance vs iterasi

PIC: Rafly (Data & Visualisasi)
Kolaborasi: Jefri (layout & integrasi)
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


VEHICLE_COLORS = ["#E74C3C", "#2ECC71", "#3498DB", "#F39C12", "#9B59B6"]

class SummaryCard(QWidget):
    """
    Widget kartu ringkasan satu metrik (label + nilai besar).

    Contoh tampilan:
      ┌─────────────────┐
      │  Total Jarak    │
      │   24.7 km       │
      └─────────────────┘
    """

    def __init__(self, title: str, value: str = "—", unit: str = ""):
        super().__init__()

        # GroupBox sebagai border kartu
        box = QGroupBox(title)
        box_layout = QVBoxLayout()
        box_layout.setAlignment(Qt.AlignCenter)

        # Label nilai — font besar, bold, warna aksen
        self._value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        self._value_label.setFont(value_font)
        self._value_label.setAlignment(Qt.AlignCenter)
        self._value_label.setStyleSheet("color: #2980B9;")

        # Label unit — font kecil, abu-abu
        self._unit_label = QLabel(unit)
        unit_font = QFont()
        unit_font.setPointSize(9)
        self._unit_label.setFont(unit_font)
        self._unit_label.setAlignment(Qt.AlignCenter)
        self._unit_label.setStyleSheet("color: #888888;")

        box_layout.addWidget(self._value_label)
        box_layout.addWidget(self._unit_label)
        box.setLayout(box_layout)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(box)
        self.setLayout(outer)

    def update_value(self, value: str, unit: str = ""):
        """Update teks label nilai dan unit."""
        self._value_label.setText(value)
        self._unit_label.setText(unit)

class ResultPanel(QWidget):
    """
    Panel lengkap yang menampilkan semua hasil optimasi.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # --- Judul ---
        title = QLabel("Hasil Optimasi")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        # --- Baris kartu ringkasan ---
        self.card_distance = SummaryCard("Total Jarak", "—", "km")
        self.card_time = SummaryCard("Waktu Komputasi", "—", "detik")
        self.card_vehicles = SummaryCard("Kendaraan Aktif", "—", "unit")

        card_row = QHBoxLayout()
        card_row.addWidget(self.card_distance)
        card_row.addWidget(self.card_time)
        card_row.addWidget(self.card_vehicles)
        main_layout.addLayout(card_row)

        # --- Tab widget ---
        self.tabs = QTabWidget()

        self.route_table = self._build_route_table()
        self.priority_table = self._build_priority_table()
        self.convergence_canvas, self.conv_ax = self._build_convergence_chart()

        self.tabs.addTab(self.route_table, "Rute")
        self.tabs.addTab(self.priority_table, "Prioritas Paket")
        self.tabs.addTab(self.convergence_canvas, "Konvergensi")

        main_layout.addWidget(self.tabs)

        # --- Tombol ekspor ---
        self.btn_export = QPushButton("Ekspor CSV")
        self.btn_export.setEnabled(False)
        main_layout.addWidget(self.btn_export)

        self.setLayout(main_layout)
        self.current_solution = None

    # ------------------------------------------------------------------
    # BUILD HELPERS
    # ------------------------------------------------------------------

    def _build_route_table(self) -> QTableWidget:
        """Buat QTableWidget untuk menampilkan rute."""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "No", "Kendaraan", "Urutan Rute", "Jarak (km)", "Muatan (kg)"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table


   def _build_priority_table(self) -> QTableWidget:
        """Buat QTableWidget untuk menampilkan prioritas Fuzzy setiap node."""
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "No", "Nama Lokasi", "Deadline (jam)", "Berat (kg)", "Prioritas", "Label"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        return table


     def _build_convergence_chart(self):
        """
        Buat grafik konvergensi menggunakan matplotlib.
        Return tuple (FigureCanvas, ax).
        """
        fig = Figure(figsize=(4, 3))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Iterasi", fontsize=9)
        ax.set_ylabel("Jarak Terbaik (m)", fontsize=9)
        ax.set_title("Grafik Konvergensi ACO", fontsize=10, fontweight="bold")
        ax.text(0.5, 0.5, "Belum ada data",
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=10, style="italic", color="#AAAAAA")
        fig.tight_layout()
        canvas.draw()
        return canvas, ax

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------
    def update_results(self, solution: dict, nodes: list, elapsed_time: float):
        """
        Update seluruh panel dengan data hasil optimasi baru.

        Parameter:
          solution     : dict dari ACOSolver.solve()
          nodes        : list[DeliveryNode] dengan priority sudah terisi
          elapsed_time : float waktu komputasi dalam detik
        """
        total_km = solution.get("distance", 0) / 1000.0
        active_vehicles = sum(1 for r in solution.get("routes", []) if r)

        self.card_distance.update_value(f"{total_km:.2f}", "km")
        self.card_time.update_value(f"{elapsed_time:.1f}", "detik")
        self.card_vehicles.update_value(str(active_vehicles), "unit")

        self._fill_route_table(solution, nodes)
        self._fill_priority_table(nodes)
        self._plot_convergence(solution.get("history", []))

        self.current_solution = solution
        self.btn_export.setEnabled(True)

    def _fill_route_table(self, solution: dict, nodes: list = None):
        """Isi tabel rute dengan data solusi."""
        self.route_table.setRowCount(0)

        # Bangun node_map untuk lookup nama dan berat
        node_map = {}
        if nodes:
            for n in nodes:
                node_map[n.node_id] = n

        routes = solution.get("routes", [])

        for vehicle_idx, route in enumerate(routes):
            if not route:
                continue

            row = self.route_table.rowCount()
            self.route_table.insertRow(row)

            # Urutan rute sebagai string
            node_names = []
            total_weight = 0.0
            for node_id in route:
                if node_id in node_map:
                    node_names.append(node_map[node_id].name)
                    total_weight += node_map[node_id].weight_kg
                else:
                    node_names.append(str(node_id))

            route_str = "Depot → " + " → ".join(node_names) + " → Depot"

            # Jarak per rute: proporsional dari total (estimasi)
            # Catatan: jarak per rute tidak tersedia di solution dict,
            # yang ada hanya total. Ditampilkan "—" per rute.
            cells = [
                str(row + 1),
                f"Kendaraan {vehicle_idx + 1}",
                route_str,
                "—",
                f"{total_weight:.1f}"
            ]

            color = QColor(VEHICLE_COLORS[vehicle_idx % len(VEHICLE_COLORS)])
            color.setAlpha(40)  # warna transparan untuk background baris

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setBackground(color)
                if col in (0, 1, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                self.route_table.setItem(row, col, item)

    def _fill_priority_table(self, nodes: list):
        """Isi tabel prioritas Fuzzy."""
        self.priority_table.setRowCount(0)

        for i, node in enumerate(nodes):
            row = self.priority_table.rowCount()
            self.priority_table.insertRow(row)

            priority = getattr(node, "priority", 0.0)

            # Tentukan label dan warna berdasarkan nilai prioritas
            if priority >= 66:
                label = "Tinggi"
                label_color = QColor("#FFCCCC")
            elif priority >= 33:
                label = "Sedang"
                label_color = QColor("#FFFACC")
            else:
                label = "Rendah"
                label_color = QColor("#CCFFCC")

            cells = [
                str(i + 1),
                node.name,
                f"{node.deadline_h:.1f}",
                f"{node.weight_kg:.1f}",
                f"{priority:.2f}",
                label
            ]

            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col in (0, 2, 3, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                # Warnai sel Label saja
                if col == 5:
                    item.setBackground(label_color)
                self.priority_table.setItem(row, col, item)

    def _plot_convergence(self, history: list):
        """Plot grafik konvergensi (best distance per iterasi)."""
        self.conv_ax.clear()

        if not history:
            self.conv_ax.text(0.5, 0.5, "Belum ada data",
                              transform=self.conv_ax.transAxes,
                              ha="center", va="center",
                              fontsize=10, style="italic", color="#AAAAAA")
            self.convergence_canvas.draw()
            return

        iterations = list(range(1, len(history) + 1))

        # Garis utama
        self.conv_ax.plot(iterations, history,
                          color="#2980B9", linewidth=1.8, zorder=3)

        # Shaded area di bawah kurva
        self.conv_ax.fill_between(iterations, history,
                                  alpha=0.2, color="#2980B9", zorder=2)

        # Tandai titik minimum
        min_val = min(history)
        min_iter = history.index(min_val) + 1
        self.conv_ax.plot(min_iter, min_val,
                          marker="o", color="#E74C3C",
                          markersize=7, zorder=4)
        self.conv_ax.annotate(
            f"{min_val:.0f} m",
            xy=(min_iter, min_val),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=8,
            color="#E74C3C",
            arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=1)
        )

        self.conv_ax.set_xlabel("Iterasi", fontsize=9)
        self.conv_ax.set_ylabel("Jarak Terbaik (m)", fontsize=9)
        self.conv_ax.set_title("Grafik Konvergensi ACO", fontsize=10, fontweight="bold")
        self.conv_ax.tick_params(labelsize=8)
        self.conv_ax.figure.tight_layout()
        self.convergence_canvas.draw()

    def clear(self):
        """Reset seluruh panel ke kondisi awal."""
        self.card_distance.update_value("—", "km")
        self.card_time.update_value("—", "detik")
        self.card_vehicles.update_value("—", "unit")

        self.route_table.setRowCount(0)
        self.priority_table.setRowCount(0)

        self._plot_convergence([])

        self.current_solution = None
        self.btn_export.setEnabled(False)
