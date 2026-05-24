"""
gui/map_canvas.py — Kanvas Peta Real dengan PyQtWebEngine + Folium
==================================================================
Menampilkan peta OpenStreetMap nyata menggunakan:
  - folium        : generate HTML map dengan tile OSM
  - PyQtWebEngine : embed browser di dalam GUI PyQt5
  - QWebChannel   : komunikasi JavaScript ↔ Python untuk klik peta

Fitur:
  - Peta real OpenStreetMap (full height, tanpa bar terpisah)
  - Klik peta → otomatis tambah lokasi ke tabel input
  - Marker warna berdasarkan prioritas Fuzzy
  - Rute per kendaraan dengan warna berbeda
  - Popup info setiap marker
  - Info "klik untuk tambah lokasi" sebagai overlay di dalam peta

PIC: Rafly (Data & Visualisasi)
Kolaborasi: Jefri (integrasi ke main_window)
"""

import os
import tempfile

import folium
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QUrl, QFile, QIODevice

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

        # Layout: web_view mengisi seluruh widget tanpa widget lain
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Web view
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_load_finished)

        layout.addWidget(self.web_view)
        self.setLayout(layout)

        # QWebChannel — komunikasi JS ↔ Python
        self.channel = QWebChannel()
        self.bridge  = MapBridge()
        self.channel.registerObject("bridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        self.bridge.location_clicked.connect(self.location_clicked)

        # State internal
        self.current_nodes    = []
        self.current_solution = None
        self._temp_file       = None

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
        """Inject qwebchannel.js inline ke HTML."""
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

    def _on_load_finished(self, ok: bool):
        """Inject JS untuk setup QWebChannel + click handler setelah halaman load."""
        if not ok:
            return

        js = """
        (function() {
            if (typeof QWebChannel === 'undefined') return;

            new QWebChannel(qt.webChannelTransport, function(channel) {
                var bridge = channel.objects.bridge;
                if (!bridge) return;

                var mapObj = null;
                for (var key in window) {
                    try {
                        if (key.startsWith('map_') &&
                            window[key] !== null &&
                            typeof window[key].on === 'function') {
                            mapObj = window[key];
                            break;
                        }
                    } catch(e) {}
                }

                if (mapObj) {
                    mapObj.on('click', function(e) {
                        bridge.onMapClick(e.latlng.lat, e.latlng.lng);
                    });
                    mapObj.getContainer().style.cursor = 'crosshair';
                }
            });
        })();
        """
        self.web_view.page().runJavaScript(js)

    def _build_base_map(self, center_lat=-5.39, center_lon=105.26,
                        zoom=13) -> folium.Map:
        """Buat folium Map dengan tile OpenStreetMap + info overlay di dalam peta."""
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles="OpenStreetMap",
            prefer_canvas=True
        )

        # Info overlay di dalam peta — tidak memakan ruang layout Qt
        info_html = (
            '<div style="position:fixed;bottom:30px;left:50%;'
            'transform:translateX(-50%);background:rgba(255,255,255,0.88);'
            'padding:6px 18px;border-radius:20px;'
            'box-shadow:0 2px 8px rgba(0,0,0,.18);'
            'z-index:9999;font-family:Arial;font-size:12px;color:#2980B9;'
            'pointer-events:none;">'
            '🗺️&nbsp; Klik pada peta untuk menambah lokasi pengiriman'
            '</div>'
        )
        m.get_root().html.add_child(folium.Element(info_html))
        return m

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
        """Tampilkan peta kosong dengan marker contoh depot."""
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
        """
        m = self.plot_nodes(nodes, depot, _skip_render=True)

        node_map              = {n.node_id: n for n in nodes}
        node_map[depot.node_id] = depot
        routes                = solution.get("routes", [])
        total_dist_km         = solution.get("distance", 0) / 1000.0

        for vehicle_idx, route in enumerate(routes):
            if not route:
                continue

            color      = VEHICLE_COLORS[vehicle_idx % len(VEHICLE_COLORS)]
            full_route = [depot.node_id] + list(route) + [depot.node_id]

            coords = [
                [node_map[nid].lat, node_map[nid].lon]
                for nid in full_route if nid in node_map
            ]

            if len(coords) >= 2:
                folium.PolyLine(
                    locations=coords,
                    color=color,
                    weight=5,
                    opacity=0.85,
                    tooltip=f"Kendaraan {vehicle_idx + 1}",
                ).add_to(m)

                # Panah arah di midpoint setiap segmen menggunakan DivIcon
                # (RegularPolygonMarker deprecated — tidak kompatibel Leaflet >= 1.8)
                import math as _math
                for i in range(len(coords) - 1):
                    mid = [
                        (coords[i][0] + coords[i+1][0]) / 2,
                        (coords[i][1] + coords[i+1][1]) / 2,
                    ]
                    # Hitung sudut rotasi panah berdasarkan arah segmen
                    dy = coords[i+1][0] - coords[i][0]
                    dx = coords[i+1][1] - coords[i][1]
                    angle = _math.degrees(_math.atan2(dx, dy))

                    arrow_html = (
                        f'<div style="'
                        f'width:0;height:0;'
                        f'border-left:6px solid transparent;'
                        f'border-right:6px solid transparent;'
                        f'border-bottom:12px solid {color};'
                        f'transform:rotate({angle:.1f}deg);'
                        f'opacity:0.85;'
                        f'"></div>'
                    )
                    folium.Marker(
                        location=mid,
                        icon=folium.DivIcon(
                            html=arrow_html,
                            icon_size=(12, 12),
                            icon_anchor=(6, 6),
                        )
                    ).add_to(m)

        # Banner total jarak di atas peta
        banner = (
            f'<div style="position:fixed;top:12px;left:50%;'
            f'transform:translateX(-50%);background:white;padding:8px 18px;'
            f'border-radius:20px;box-shadow:0 2px 10px rgba(0,0,0,.25);'
            f'z-index:9999;font-family:Arial;font-size:13px;font-weight:bold;'
            f'color:#1A1A2E;pointer-events:none;">'
            f'🚚 Rute Optimal &nbsp;|&nbsp; Total Jarak: {total_dist_km:.2f} km'
            f'</div>'
        )
        m.get_root().html.add_child(folium.Element(banner))

        self.current_solution = solution
        self._render(m)

    def animate_iteration(self, pheromone_matrix, nodes: list, depot):
        """
        (Fitur opsional) Visualisasi intensitas feromon per iterasi.
        Hanya diimplementasikan jika waktu pengerjaan mencukupi.
        """
        pass

    def clear(self):
        """Reset canvas ke empty state."""
        self.current_nodes    = []
        self.current_solution = None
        self._draw_empty_state()

    def save_figure(self, filepath: str):
        """Simpan peta sebagai file HTML."""
        if self._temp_file and os.path.exists(self._temp_file):
            import shutil
            shutil.copy(self._temp_file, filepath)