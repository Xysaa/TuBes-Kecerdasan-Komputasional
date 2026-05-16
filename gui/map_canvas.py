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
        super().__init__(parent)

        # Buat figure dan canvas matplotlib
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Toolbar zoom/pan bawaan matplotlib
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Layout: toolbar di atas, canvas di bawah
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # State internal
        self.current_nodes = []
        self.current_solution = None

        # Hubungkan event hover untuk tooltip
        self._hover_annotation = None
        self._node_scatter = None
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

        self._draw_empty_state()

     def _draw_empty_state(self):
        """Tampilkan placeholder saat belum ada data."""
        self.ax.clear()
        self.ax.set_facecolor("#F8F9FA")
        self.figure.patch.set_facecolor("#F8F9FA")

        self.ax.text(
            0.5, 0.5,
            "Tambahkan lokasi dan jalankan optimasi",
            transform=self.ax.transAxes,
            ha="center", va="center",
            fontsize=13, style="italic",
            color="#AAAAAA"
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for spine in self.ax.spines.values():
            spine.set_edgecolor("#DDDDDD")

        self.canvas.draw()

    def _build_node_map(self, nodes, depot):
        """
        Bangun dict {node_id: DeliveryNode} dari nodes + depot.
        Dipakai untuk lookup cepat saat render rute.
        """
        node_map = {n.node_id: n for n in nodes}
        node_map[depot.node_id] = depot
        return node_map

    def _on_hover(self, event):
        """
        Tampilkan tooltip nama & prioritas saat kursor hover di atas node.
        Hanya aktif kalau sudah ada scatter plot node.
        """
        if event.inaxes != self.ax or self._node_scatter is None:
            if self._hover_annotation:
                self._hover_annotation.set_visible(False)
                self.canvas.draw_idle()
            return

        cont, ind = self._node_scatter.contains(event)
        if cont:
            idx = ind["ind"][0]
            # _scatter_meta disimpan saat plot_nodes dipanggil
            name, priority = self._scatter_meta[idx]
            x = self._node_scatter.get_offsets()[idx][0]
            y = self._node_scatter.get_offsets()[idx][1]

            if self._hover_annotation is None:
                self._hover_annotation = self.ax.annotate(
                    "",
                    xy=(x, y),
                    xytext=(15, 15),
                    textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.4", fc="white",
                              ec="#CCCCCC", alpha=0.9),
                    fontsize=9,
                    zorder=10
                )

            self._hover_annotation.set_text(
                f"{name}\nPrioritas: {priority:.1f}"
            )
            self._hover_annotation.xy = (x, y)
            self._hover_annotation.set_visible(True)
        else:
            if self._hover_annotation:
                self._hover_annotation.set_visible(False)

        self.canvas.draw_idle()

    # ------------------------------------------------------------------
    # PUBLIC API
    # ---------------
    def plot_nodes(self, nodes: list, depot, _skip_draw=False):
        """
        Tampilkan semua titik lokasi di peta (sebelum ACO dijalankan).

        Parameter:
          nodes      : list[DeliveryNode] — titik pengiriman
          depot      : DeliveryNode       — titik depot
          _skip_draw : bool               — True jika dipanggil dari
                                           plot_solution (draw ditunda)
        """
        self.ax.clear()
        self._hover_annotation = None
        self._node_scatter = None
        self._scatter_meta = []

        self.ax.set_facecolor("#F0F4F8")
        self.figure.patch.set_facecolor("#FFFFFF")

        # --- Plot delivery nodes ---
        lons = [n.lon for n in nodes]
        lats = [n.lat for n in nodes]
        priorities = [n.priority for n in nodes]

        scatter = self.ax.scatter(
            lons, lats,
            c=priorities,
            cmap="RdYlGn_r",
            vmin=0, vmax=100,
            s=90, zorder=5,
            edgecolors="white", linewidths=0.8
        )
        self._node_scatter = scatter
        self._scatter_meta = [(n.name, n.priority) for n in nodes]

        # Anotasi nama node
        for n in nodes:
            self.ax.annotate(
                n.name,
                xy=(n.lon, n.lat),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=7.5,
                color="#333333",
                zorder=6
            )

        # --- Plot depot ---
        self.ax.plot(
            depot.lon, depot.lat,
            marker="*",
            markersize=16,
            color="#1A1A2E",
            zorder=7,
            label="Depot",
            linestyle="None"
        )
        self.ax.annotate(
            depot.name,
            xy=(depot.lon, depot.lat),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
            color="#1A1A2E",
            zorder=8
        )

        # --- Colorbar prioritas ---
        cbar = self.figure.colorbar(scatter, ax=self.ax, pad=0.02, shrink=0.8)
        cbar.set_label("Prioritas Pengiriman", fontsize=9)
        cbar.ax.tick_params(labelsize=8)

        # --- Label & judul ---
        self.ax.set_xlabel("Longitude", fontsize=9)
        self.ax.set_ylabel("Latitude", fontsize=9)
        self.ax.set_title("Peta Lokasi Pengiriman", fontsize=11, fontweight="bold")
        self.ax.tick_params(labelsize=8)

        # Simpan nodes untuk dipakai plot_solution
        self.current_nodes = nodes

        if not _skip_draw:
            self.canvas.draw()

    def plot_solution(self, solution: dict, nodes: list, depot, problem):
        """
        Tampilkan rute optimal hasil ACO.

        Parameter:
          solution : dict {'routes': list[list[int]], 'distance': float, 'history': list}
          nodes    : list[DeliveryNode]
          depot    : DeliveryNode
          problem  : VRPProblem
        """
        # Gambar base layer nodes dulu (tanpa draw)
        self.plot_nodes(nodes, depot, _skip_draw=True)

        node_map = self._build_node_map(nodes, depot)
        routes = solution.get("routes", [])
        total_dist_km = solution.get("distance", 0) / 1000.0

        legend_patches = [
            mpatches.Patch(color="#1A1A2E", label="Depot ★")
        ]

        for vehicle_idx, route in enumerate(routes):
            if not route:
                continue

            color = VEHICLE_COLORS[vehicle_idx % len(VEHICLE_COLORS)]
            vehicle_label = f"Kendaraan {vehicle_idx + 1}"

            # Bangun urutan titik: depot → node1 → ... → nodeN → depot
            full_route = [depot.node_id] + route + [depot.node_id]

            for step in range(len(full_route) - 1):
                id_from = full_route[step]
                id_to = full_route[step + 1]

                if id_from not in node_map or id_to not in node_map:
                    continue

                n_from = node_map[id_from]
                n_to = node_map[id_to]

                # Garis rute
                self.ax.plot(
                    [n_from.lon, n_to.lon],
                    [n_from.lat, n_to.lat],
                    color=color, linewidth=1.8,
                    alpha=0.75, zorder=3
                )

                # Panah arah di tengah segmen
                mid_lon = (n_from.lon + n_to.lon) / 2
                mid_lat = (n_from.lat + n_to.lat) / 2
                d_lon = n_to.lon - n_from.lon
                d_lat = n_to.lat - n_from.lat

                self.ax.annotate(
                    "",
                    xy=(mid_lon + d_lon * 0.01, mid_lat + d_lat * 0.01),
                    xytext=(mid_lon - d_lon * 0.01, mid_lat - d_lat * 0.01),
                    arrowprops=dict(
                        arrowstyle="->",
                        color=color,
                        lw=1.6
                    ),
                    zorder=4
                )

            legend_patches.append(
                mpatches.Patch(color=color, label=vehicle_label)
            )

        # --- Legend & judul ---
        self.ax.legend(
            handles=legend_patches,
            loc="upper left",
            fontsize=8,
            framealpha=0.9,
            edgecolor="#CCCCCC"
        )
        self.ax.set_title(
            f"Rute Optimal — Total Jarak: {total_dist_km:.2f} km",
            fontsize=11, fontweight="bold"
        )

        self.current_solution = solution
        self.canvas.draw()

     def animate_iteration(self, pheromone_matrix, nodes: list, depot):
        """
        (Fitur opsional) Visualisasi intensitas feromon per iterasi.

        Parameter:
          pheromone_matrix : numpy array n×n feromon saat ini
          nodes            : list[DeliveryNode]
          depot            : DeliveryNode

        Catatan:
          Index 0 di pheromone_matrix = depot, 1..n = nodes,
          sesuai urutan problem.get_all_nodes().
        """
        all_nodes = [depot] + list(nodes)
        n = len(all_nodes)

        if pheromone_matrix is None or pheromone_matrix.shape != (n, n):
            return

        # Normalisasi nilai feromon ke range [0, 1] untuk opacity
        p_max = pheromone_matrix.max()
        p_min = pheromone_matrix.min()
        p_range = p_max - p_min if p_max != p_min else 1.0

        for i in range(n):
            for j in range(i + 1, n):
                intensity = (pheromone_matrix[i][j] - p_min) / p_range
                if intensity < 0.1:
                    # Skip garis yang hampir tidak terlihat
                    continue

                n_i = all_nodes[i]
                n_j = all_nodes[j]

                self.ax.plot(
                    [n_i.lon, n_j.lon],
                    [n_i.lat, n_j.lat],
                    color="#F39C12",
                    linewidth=intensity * 3,
                    alpha=intensity * 0.6,
                    zorder=2
                )

        self.canvas.draw_idle()

  def clear(self):
        """Reset canvas ke empty state."""
        self.current_nodes = []
        self.current_solution = None
        self._node_scatter = None
        self._hover_annotation = None
        self._scatter_meta = []
        self._draw_empty_state()

    def save_figure(self, filepath: str):
        """
        Simpan visualisasi saat ini ke file gambar.

        Parameter:
          filepath : str — path lengkap file output (misal: "/home/user/rute.png")
        """
        self.figure.savefig(filepath, dpi=150, bbox_inches="tight")
