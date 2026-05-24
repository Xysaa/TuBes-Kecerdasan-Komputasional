"""
data/osm_handler.py — Handler OpenStreetMap
=============================================
Bertanggung jawab untuk:
  1. Mengunduh graf jaringan jalan dari OpenStreetMap via OSMnx
  2. Menyimpan & memuat cache graf (agar tidak perlu unduh ulang)
  3. Melakukan geocoding (nama tempat → koordinat lat/lon)
  4. Memetakan koordinat ke node terdekat di graf jalan
  5. Menghitung matriks jarak jalan nyata antar semua node

Catatan Penting:
  - Graf diunduh SEKALI lalu disimpan sebagai file .graphml
  - Jarak yang digunakan adalah jarak JALAN, bukan garis lurus
  - Jika path tidak ditemukan antar dua node, gunakan fallback Haversine

PIC: Anggota 4 (Data & Visualisasi)
Kolaborasi: Anggota 1 (output matriks jarak ke ACO)

CHANGELOG:
  - FIX: Download graf dengan largest_component=True agar graf terkoneksi penuh
  - FIX: Tambah logging jumlah fallback Haversine agar mudah dideteksi
  - FIX: Gunakan ox.distance.nearest_nodes (API baru osmnx >= 1.0)
"""

import os
import math
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from core.vrp_model import DeliveryNode, VRPProblem

# Path default untuk cache graf OSM
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
DEFAULT_CACHE_FILE = os.path.join(CACHE_DIR, "osm_graph.graphml")


class OSMHandler:
    """
    Handler untuk semua operasi yang berkaitan dengan data OpenStreetMap.
    """

    def __init__(self, city: str = "Bandar Lampung, Indonesia",
                 cache_file: str = DEFAULT_CACHE_FILE):
        """
        Inisialisasi OSMHandler.

        Parameter:
          city       : Nama kota/area untuk diunduh dari OSM
          cache_file : Path file .graphml untuk menyimpan/memuat cache graf
        """
        self.city       = city
        self.cache_file = cache_file
        self.graph      = None
        self.geolocator = Nominatim(user_agent="vrp_aco_app")

        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Graph Loading
    # ──────────────────────────────────────────────────────────────────────────

    def load_graph(self, force_download: bool = False):
        """
        Muat graf jalan: dari cache jika ada, atau unduh dari OSM.

        Parameter:
          force_download: Jika True, selalu unduh ulang meski cache ada.
        """
        if os.path.exists(self.cache_file) and not force_download:
            import osmnx as ox
            print(f"Memuat graf dari cache: {self.cache_file}")
            self.graph = ox.load_graphml(self.cache_file)
            print(f"Graf berhasil dimuat: {len(self.graph.nodes)} node, "
                  f"{len(self.graph.edges)} edge.")
        else:
            self._download_graph()

    def _download_graph(self):
        """
        Unduh graf jalan dari OpenStreetMap dan simpan ke cache.

        FIX: Tambah retain_all=False (default) agar hanya komponen
        terbesar yang disimpan → dijamin strongly connected → tidak ada
        path yang putus → tidak ada fallback Haversine.
        """
        import osmnx as ox
        try:
            print(f"Mengunduh graf jalan untuk '{self.city}' dari OSM...")
            # retain_all=False (default) → ambil hanya weakly connected component terbesar
            self.graph = ox.graph_from_place(
                self.city,
                network_type='drive',
                retain_all=False,      # hanya ambil komponen terbesar
            )
            # Pastikan graf strongly connected (untuk routing dua arah)
            self.graph = ox.utils_graph.get_largest_component(
                self.graph, strongly=True
            )
            ox.save_graphml(self.graph, self.cache_file)
            print(f"Graf disimpan ke: {self.cache_file}")
            print(f"  → {len(self.graph.nodes)} node, {len(self.graph.edges)} edge")
        except ConnectionError as e:
            print(f"[ERROR] Tidak ada koneksi internet: {e}")
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Geocoding
    # ──────────────────────────────────────────────────────────────────────────

    def geocode(self, place_name: str) -> tuple:
        """
        Konversi nama tempat ke koordinat (lat, lon).

        Return:
          tuple (lat, lon) atau (None, None) jika gagal.
        """
        try:
            location = self.geolocator.geocode(place_name)
            if location:
                return (location.latitude, location.longitude)
            else:
                print(f"[WARN] Lokasi tidak ditemukan: '{place_name}'")
                return (None, None)
        except GeocoderTimedOut:
            print(f"[WARN] Geocoder timeout untuk: '{place_name}'")
            return (None, None)
        except Exception as e:
            print(f"[ERROR] Geocoding gagal untuk '{place_name}': {e}")
            return (None, None)

    # ──────────────────────────────────────────────────────────────────────────
    # Graph Snapping
    # ──────────────────────────────────────────────────────────────────────────

    def snap_to_graph(self, lat: float, lon: float) -> int:
        """
        Temukan node OSM terdekat dari koordinat lat/lon.

        Catatan: osmnx menerima (X=lon, Y=lat), bukan (lat, lon)!

        Return:
          int: ID node OSM terdekat di self.graph
        """
        import osmnx as ox
        if self.graph is None:
            raise RuntimeError(
                "Graf belum dimuat. Panggil load_graph() terlebih dahulu."
            )
        # nearest_nodes(G, X=lon, Y=lat)
        return ox.nearest_nodes(self.graph, lon, lat)

    # ──────────────────────────────────────────────────────────────────────────
    # Distance Matrix
    # ──────────────────────────────────────────────────────────────────────────

    def compute_distance_matrix(self, problem: VRPProblem) -> list:
        """
        Hitung matriks jarak jalan nyata antar semua node dalam VRPProblem.

        Node index di matriks: 0 = depot, 1..n = delivery nodes
        (urutan sesuai problem.get_all_nodes())

        Return:
          list[list[float]]: matriks n×n berisi jarak dalam meter
        """
        if self.graph is None:
            raise RuntimeError(
                "Graf belum dimuat. Panggil load_graph() terlebih dahulu."
            )

        all_nodes = problem.get_all_nodes()   # [depot, node1, ..., nodeN]
        n         = len(all_nodes)

        print(f"Snapping {n} lokasi ke graf OSM...")

        # Snap semua node ke graf OSM
        osm_ids = []
        for node in all_nodes:
            osm_id = self.snap_to_graph(node.lat, node.lon)
            node.osm_node_id = osm_id   # simpan untuk debugging
            osm_ids.append(osm_id)
            print(f"  [{node.name}] → OSM node {osm_id}")

        # Buat matriks n×n
        matrix         = np.zeros((n, n), dtype=float)
        fallback_count = 0

        print(f"Menghitung {n*n - n} pasang jarak via shortest path OSM...")

        for i in range(n):
            for j in range(n):
                if i != j:
                    dist, used_fallback = self._get_path_length(
                        osm_ids[i], osm_ids[j]
                    )
                    matrix[i][j] = dist
                    if used_fallback:
                        fallback_count += 1

        if fallback_count > 0:
            print(f"[WARN] {fallback_count} pasang node menggunakan fallback "
                  f"Haversine (jarak lurus). Coba force_download=True untuk "
                  f"memperbarui cache graf.")
        else:
            print("Semua jarak dihitung via jalan nyata (tidak ada fallback).")

        dist_list             = matrix.tolist()
        problem.dist_matrix   = dist_list
        return dist_list

    # ──────────────────────────────────────────────────────────────────────────
    # Path Length Calculation
    # ──────────────────────────────────────────────────────────────────────────

    def _get_path_length(self, node_a: int, node_b: int) -> tuple:
        """
        Hitung jarak jalan terpendek antara dua node OSM.

        Return:
          tuple (jarak_meter: float, used_fallback: bool)
        """
        import networkx as nx
        try:
            dist = nx.shortest_path_length(
                self.graph, node_a, node_b, weight='length'
            )
            return dist, False
        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            print(f"[WARN] Tidak ada path antara node {node_a} ↔ {node_b}: {e}. "
                  f"Menggunakan fallback Haversine.")
            return self._haversine_fallback(node_a, node_b), True

    def _haversine_fallback(self, node_a: int, node_b: int) -> float:
        """
        Hitung jarak garis lurus (Haversine) sebagai fallback.

        Return:
          float: Jarak dalam meter
        """
        lat_a = self.graph.nodes[node_a]['y']
        lon_a = self.graph.nodes[node_a]['x']
        lat_b = self.graph.nodes[node_b]['y']
        lon_b = self.graph.nodes[node_b]['x']

        return _haversine(lat_a, lon_a, lat_b, lon_b)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Haversine Formula
# ──────────────────────────────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Hitung jarak antara dua koordinat geografis menggunakan rumus Haversine.

    Return:
      float: Jarak dalam meter
    """
    R = 6_371_000  # Jari-jari bumi dalam meter

    phi1     = math.radians(lat1)
    phi2     = math.radians(lat2)
    d_phi    = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c