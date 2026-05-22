"""
gui/map_canvas.py — Kanvas Peta Real dengan PyQtWebEngine + Folium
==================================================================
Menampilkan peta OpenStreetMap nyata menggunakan:
  - folium        : generate HTML map dengan tile OSM
  - PyQtWebEngine : embed browser di dalam GUI PyQt5
  - QWebChannel   : komunikasi JavaScript ↔ Python untuk klik peta

Fitur:
  - Peta real OpenStreetMap
  - Klik peta → otomatis tambah lokasi ke tabel input
  - Marker warna berdasarkan prioritas Fuzzy
  - Rute per kendaraan dengan warna berbeda
  - Popup info setiap marker

PIC: Rafly (Data & Visualisasi)
Kolaborasi: Jefri (integrasi ke main_window)

CHANGELOG:
  - FIX: Rute terputus — perbaiki mapping index ACO → node objek
  - FIX: Rute hilang saat zoom — hapus prefer_canvas=True
  - FIX: Click handler inject dengan QTimer delay 500ms
"""

import os
import tempfile

import folium
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl, QFile, QIODevice, Qt, QTimer

# Warna per kendaraan (maks 5)
VEHICLE_COLORS = ["#E74C3C", "#2ECC71", "#3498DB", "#F39C12", "#9B59B6"]


# ── Bridge: jembatan JavaScript ↔ Python ─────────────────────────────────────

class MapBridge(QObject):
    """
    Objek yang bisa dipanggil dari JavaScript via QWebChannel.
    Ketika user klik peta, JS memanggil onMapClick() → Python emit sinyal.
    """
    location_clicked = pyqtSignal(float, float)  # lat, lon

    @pyqtSlot(float, float)
    def onMapClick(self, lat: float, lon: float):
        self.location_clicked.emit(lat, lon)


# ── Main Widget ───────────────────────────────────────────────────────────────

class MapCanvas(QWidget):
    """
    Widget peta real berbasis PyQtWebEngine + Folium.
    Emit sinyal location_clicked(lat, lon) ketika user klik peta.
    """

    location_clicked = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Info bar
        self.info_label = QLabel("🗺️  Klik pada peta untuk menambah lokasi pengiriman")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(
            "background:#EBF5FB; padding:6px; font-size:11px; color:#2980B9; "
            "border-bottom:1px solid #AED6F1;"
        )

        # Web view
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_load_finished)

        # QWebChannel — komunikasi JS ↔ Python
        self.channel = QWebChannel()
        self.bridge  = MapBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        self.bridge.location_clicked.connect(self.location_clicked)

        layout.addWidget(self.info_label)
        layout.addWidget(self.web_view)
        self.setLayout(layout)

        self.current_nodes    = []
        self.current_solution = None
        self._temp_file       = None
        self._last_map        = None

        self._draw_empty_state()

    # ── Private ───────────────────────────────────────────────────────────────

    def _get_webchannel_js(self) -> str:
        """Baca qwebchannel.js dari resource Qt."""
        f = QFile(":/qtwebchannel/qwebchannel.js")
        if f.open(QIODevice.ReadOnly):
            content = bytes(f.readAll()).decode("utf-8")
            f.close()
            return content
        return ""

    def _inject_scripts(self, html: str) -> str:
        """
        Inject qwebchannel.js inline ke HTML agar tidak perlu akses qrc://
        dari konteks file lokal yang bisa diblokir browser engine.
        """
        webchannel_js = self._get_webchannel_js()
        script_block = f"""
        <script>
        /* ── QWebChannel inline ── */
        {webchannel_js}
        </script>
        """
        return html.replace("</head>", script_block + "</head>", 1)

    def _render(self, folium_map: folium.Map):
        """Render folium map → file HTML sementara → tampilkan di web_view."""
        html = folium_map.get_root().render()
        html = self._inject_scripts(html)

        # Hapus temp file lama
        if self._temp_file:
            try:
                os.unlink(self._temp_file)
            except Exception:
                pass

        tmp = tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        )
        tmp.write(html)
        tmp.close()
        self._temp_file = tmp.name

        self.web_view.load(QUrl.fromLocalFile(self._temp_file))
        self._last_map = folium_map

    def _on_load_finished(self, ok: bool):
        """
        Dipanggil setelah halaman HTML selesai dimuat.
        Delay 500ms agar Leaflet selesai inisialisasi objek map_*.
        """
        if not ok:
            return
        QTimer.singleShot(500, self._inject_click_handler)

    def _inject_click_handler(self):
        """
        Inject JavaScript untuk setup QWebChannel + Leaflet click handler.
        Dipanggil 500ms setelah halaman selesai load.
        """
        js = """
        (function() {
            if (typeof QWebChannel === 'undefined') {
                console.error('[MapCanvas] QWebChannel tidak tersedia');
                return;
            }

            new QWebChannel(qt.webChannelTransport, function(channel) {
                var bridge = channel.objects.bridge;
                if (!bridge) {
                    console.error('[MapCanvas] Bridge tidak ditemukan di channel');
                    return;
                }

                /* Cari objek Leaflet map — harus punya .on() dan .getCenter() */
                var mapObj = null;
                var keys = Object.keys(window);
                for (var i = 0; i < keys.length; i++) {
                    var key = keys[i];
                    if (!key.startsWith('map_')) continue;
                    try {
                        var obj = window[key];
                        if (obj &&
                            typeof obj.on === 'function' &&
                            typeof obj.getCenter === 'function') {
                            mapObj = obj;
                            break;
                        }
                    } catch(e) {}
                }

                if (!mapObj) {
                    console.error('[MapCanvas] Objek peta Leaflet tidak ditemukan');
                    return;
                }

                mapObj.on('click', function(e) {
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;
                    console.log('[MapCanvas] Klik terdeteksi:', lat, lng);
                    bridge.onMapClick(lat, lng);
                });

                mapObj.getContainer().style.cursor = 'crosshair';
                console.log('[MapCanvas] Click handler berhasil dipasang');
            });
        })();
        """
        self.web_view.page().runJavaScript(js)

    def _build_base_map(self, center_lat=-5.39, center_lon=105.26,
                        zoom=13) -> folium.Map:
        """
        Buat folium Map dengan tile OpenStreetMap.
        CATATAN: prefer_canvas=True DIHAPUS — menyebabkan PolyLine hilang saat zoom.
        """
        return folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles="OpenStreetMap",
        )

    def _priority_icon(self, priority: float) -> folium.Icon:
        """Return folium Icon berdasarkan skor prioritas."""
        if priority >= 67:
            return folium.Icon(color="red",    icon="arrow-up",   prefix="fa")
        elif priority >= 34:
            return folium.Icon(color="orange", icon="minus",      prefix="fa")
        else:
            return folium.Icon(color="green",  icon="arrow-down", prefix="fa")

    # ── Public API ────────────────────────────────────────────────────────────

    def _draw_empty_state(self):
        """Tampilkan peta kosong dengan instruksi."""
        m = self._build_base_map()
        folium.Marker(
            location=[-5.3971, 105.2668],
            tooltip="Ini adalah posisi Depot Pusat (contoh)",
            popup="Klik di mana saja pada peta untuk menambah lokasi",
            icon=folium.Icon(color="gray", icon="info-sign")
        ).add_to(m)
        self._render(m)

    def plot_nodes(self, nodes: list, depot, _skip_render=False):
        """
        Tampilkan marker semua lokasi di peta real.

        Return:
          folium.Map — map object (dipakai oleh plot_solution)
        """
        all_lats = [depot.lat] + [n.lat for n in nodes]
        all_lons = [depot.lon] + [n.lon for n in nodes]
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)

        m = self._build_base_map(center_lat, center_lon, zoom=14)

        # Depot marker
        folium.Marker(
            location=[depot.lat, depot.lon],
            popup=folium.Popup(
                f"<b>⭐ {depot.name}</b><br><i>Depot / Titik Awal</i>",
                max_width=200
            ),
            tooltip=f"⭐ {depot.name} (Depot)",
            icon=folium.Icon(color="black", icon="home", prefix="fa")
        ).add_to(m)

        # Delivery node markers
        for node in nodes:
            priority = getattr(node, "priority", 0.0)
            label    = ("🔴 Tinggi" if priority >= 67
                        else "🟡 Sedang" if priority >= 34
                        else "🟢 Rendah")

            popup_html = (
                f"<b>{node.name}</b><br>"
                f"Berat: <b>{node.weight_kg} kg</b><br>"
                f"Deadline: <b>{node.deadline_h} jam</b><br>"
                f"Prioritas: <b>{priority:.1f}</b> {label}"
            )

            folium.Marker(
                location=[node.lat, node.lon],
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{node.name} | Prioritas: {priority:.0f}",
                icon=self._priority_icon(priority)
            ).add_to(m)

        self.current_nodes = nodes

        if not _skip_render:
            self._render(m)

        return m

    def plot_solution(self, solution: dict, nodes: list, depot, problem):
        """
        Tampilkan rute optimal di atas peta real dengan polyline berwarna.

        FIX: ACO mengembalikan index matriks (0=depot, 1..n=delivery node).
        Mapping dilakukan via index ke all_nodes list — bukan via node_id dict
        — sehingga semua node selalu ditemukan dan rute tidak terputus.
        """
        m = self.plot_nodes(nodes, depot, _skip_render=True)

        # ── FIX: index-based mapping ──────────────────────────────────────────
        # problem.get_all_nodes() → [depot, node1, node2, ...]
        # Index 0 = depot, index 1..n = delivery nodes
        # HARUS sama urutannya dengan yang dipakai ACO saat build dist_matrix
        all_nodes     = problem.get_all_nodes()
        routes        = solution.get("routes", [])
        total_dist_km = solution.get("distance", 0) / 1000.0

        for vehicle_idx, route in enumerate(routes):
            if not route:
                continue

            color = VEHICLE_COLORS[vehicle_idx % len(VEHICLE_COLORS)]

            # route = list index matriks, misal [2, 1, 3]
            # full_route_idx: depot(0) → 2 → 1 → 3 → depot(0)
            full_route_idx = [0] + list(route) + [0]

            # Ambil koordinat via index → all_nodes
            coords = []
            for idx in full_route_idx:
                if 0 <= idx < len(all_nodes):
                    node = all_nodes[idx]
                    coords.append([node.lat, node.lon])
                else:
                    print(f"[WARN] plot_solution: index {idx} di luar "
                          f"jangkauan all_nodes (len={len(all_nodes)})")

            if len(coords) >= 2:
                # Garis rute — tetap ada saat zoom karena prefer_canvas dihapus
                folium.PolyLine(
                    locations=coords,
                    color=color,
                    weight=5,
                    opacity=0.85,
                    tooltip=f"Kendaraan {vehicle_idx + 1}",
                ).add_to(m)

                # Panah arah di setiap midpoint segmen
                for i in range(len(coords) - 1):
                    mid = [
                        (coords[i][0] + coords[i + 1][0]) / 2,
                        (coords[i][1] + coords[i + 1][1]) / 2,
                    ]
                    folium.RegularPolygonMarker(
                        location=mid,
                        number_of_sides=3,
                        radius=7,
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.9,
                        rotation=45
                    ).add_to(m)

        # Banner judul di atas peta
        banner = (
            f'<div style="position:fixed;top:12px;left:50%;'
            f'transform:translateX(-50%);background:white;padding:8px 18px;'
            f'border-radius:20px;box-shadow:0 2px 10px rgba(0,0,0,.25);'
            f'z-index:9999;font-family:Arial;font-size:13px;font-weight:bold;'
            f'color:#1A1A2E;">'
            f'🚚 Rute Optimal &nbsp;|&nbsp; Total Jarak: {total_dist_km:.2f} km'
            f'</div>'
        )
        m.get_root().html.add_child(folium.Element(banner))

        self.current_solution = solution
        self._render(m)

    def clear(self):
        """Reset ke empty state."""
        self.current_nodes    = []
        self.current_solution = None
        self._draw_empty_state()

    def save_figure(self, filepath: str):
        """Simpan peta sebagai file HTML."""
        if self._temp_file and os.path.exists(self._temp_file):
            import shutil
            shutil.copy(self._temp_file, filepath)