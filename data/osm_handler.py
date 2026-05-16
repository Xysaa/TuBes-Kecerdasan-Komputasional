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
  - Jika path tidak ditemukan antar dua node, gunakan fallback Euclidean

PIC: Anggota 4 (Data & Visualisasi)
Kolaborasi: Anggota 1 (output matriks jarak ke ACO)
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
        self.city = city
        self.cache_file = cache_file
        self.graph = None
        self.geolocator = Nominatim(user_agent="vrp_aco_app")

        # Buat direktori cache jika belum ada
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Graph Loading
    # ──────────────────────────────────────────────────────────────────────────

    def load_graph(self, force_download: bool = False):
        """
        Muat graf jalan: dari cache jika ada, atau unduh dari OSM.

        Parameter:
          force_download: Jika True, selalu unduh ulang meski cache ada
        """
        if os.path.exists(self.cache_file) and not force_download:
            import osmnx as ox
            print(f"Memuat graf dari cache: {self.cache_file}")
            self.graph = ox.load_graphml(self.cache_file)
            print("Graf berhasil dimuat dari cache.")
        else:
            self._download_graph()

    def _download_graph(self):
        """
        Unduh graf jalan dari OpenStreetMap dan simpan ke cache.
        """
        import osmnx as ox
        try:
            print(f"Mengunduh graf jalan untuk '{self.city}' dari OSM...")
            self.graph = ox.graph_from_place(self.city, network_type='drive')
            ox.save_graphml(self.graph, self.cache_file)
            print(f"Graf berhasil diunduh dan disimpan ke: {self.cache_file}")
        except ConnectionError as e:
            print(f"[ERROR] Tidak ada koneksi internet. Gagal mengunduh graf: {e}")
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Geocoding
    # ──────────────────────────────────────────────────────────────────────────

    def geocode(self, place_name: str) -> tuple:
        """
        Konversi nama tempat ke koordinat (lat, lon).

        Parameter:
          place_name: Nama lokasi, misal "Pasar Tengah, Bandar Lampung"

        Return:
          tuple (lat: float, lon: float) atau (None, None) jika gagal
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

        Parameter:
          lat, lon: Koordinat geografis

        Return:
          int: ID node OSM terdekat di self.graph

        Catatan: osmnx menerima (X=lon, Y=lat), bukan (lat, lon)!
        """
        import osmnx as ox
        if self.graph is None:
            raise RuntimeError(
                "Graf belum dimuat. Panggil load_graph() terlebih dahulu."
            )
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

        all_nodes = problem.get_all_nodes()
        n = len(all_nodes)

        # Snap semua node ke graf OSM dan simpan osm_node_id ke masing-masing node
        osm_ids = []
        for node in all_nodes:
            osm_id = self.snap_to_graph(node.lat, node.lon)
            node.osm_node_id = osm_id
            osm_ids.append(osm_id)

        # Buat matriks n×n (diagonal = 0)
        matrix = np.zeros((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self._get_path_length(osm_ids[i], osm_ids[j])

        # Simpan ke problem dan kembalikan sebagai nested list
        dist_list = matrix.tolist()
        problem.dist_matrix = dist_list
        return dist_list

    # ──────────────────────────────────────────────────────────────────────────
    # Path Length Calculation
    # ──────────────────────────────────────────────────────────────────────────

    def _get_path_length(self, node_a: int, node_b: int) -> float:
        """
        Hitung jarak jalan terpendek antara dua node OSM.

        Parameter:
          node_a, node_b: ID node OSM

        Return:
          float: Jarak dalam meter
        """
        import networkx as nx
        try:
            return nx.shortest_path_length(
                self.graph, node_a, node_b, weight='length'
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # Fallback ke jarak Euclidean (Haversine) jika path tidak ada
            print(
                f"[WARN] Tidak ada path antara node {node_a} dan {node_b}. "
                "Menggunakan fallback Euclidean."
            )
            return self._euclidean_fallback(node_a, node_b)

    def _euclidean_fallback(self, node_a: int, node_b: int) -> float:
        """
        Hitung jarak Euclidean (garis lurus) sebagai fallback menggunakan
        rumus Haversine untuk akurasi pada koordinat geografis.

        Return:
          float: Jarak dalam meter
        """
        # Ambil koordinat dari graf (y=lat, x=lon dalam OSMnx)
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
    Hitung jarak antara dua titik koordinat geografis menggunakan rumus Haversine.
    Referensi: https://en.wikipedia.org/wiki/Haversine_formula

    Return:
      float: Jarak dalam meter
    """
    R = 6_371_000  # Jari-jari bumi dalam meter

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
