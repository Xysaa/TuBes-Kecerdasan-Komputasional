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
        TODO:
        - Simpan self.city dan self.cache_file
        - Inisialisasi self.graph = None
        - Inisialisasi self.geolocator = Nominatim(user_agent="vrp_aco_app")
        - Buat direktori cache jika belum ada (os.makedirs)
        """
        pass

    def load_graph(self, force_download: bool = False):
        """
        Muat graf jalan: dari cache jika ada, atau unduh dari OSM.

        Parameter:
          force_download: Jika True, selalu unduh ulang meski cache ada

        TODO:
        - Jika cache ada DAN force_download=False:
            import osmnx as ox
            self.graph = ox.load_graphml(self.cache_file)
            print("Graf dimuat dari cache.")
        - Jika tidak:
            Panggil self._download_graph()
        """
        pass

    def _download_graph(self):
        """
        Unduh graf jalan dari OpenStreetMap dan simpan ke cache.

        TODO:
        - import osmnx as ox
        - self.graph = ox.graph_from_place(self.city, network_type='drive')
        - Simpan ke cache: ox.save_graphml(self.graph, self.cache_file)
        - Print pesan sukses
        - Tangani ConnectionError jika tidak ada internet
        """
        pass

    def geocode(self, place_name: str) -> tuple:
        """
        Konversi nama tempat ke koordinat (lat, lon).

        Parameter:
          place_name: Nama lokasi, misal "Pasar Tengah, Bandar Lampung"

        Return:
          tuple (lat: float, lon: float) atau (None, None) jika gagal

        TODO:
        - Gunakan self.geolocator.geocode(place_name)
        - Jika berhasil: return (location.latitude, location.longitude)
        - Jika gagal / None: return (None, None)
        - Tangani exception GeocoderTimedOut
        """
        pass

    def snap_to_graph(self, lat: float, lon: float) -> int:
        """
        Temukan node OSM terdekat dari koordinat lat/lon.

        Parameter:
          lat, lon: Koordinat geografis

        Return:
          int: ID node OSM terdekat di self.graph

        TODO:
        - import osmnx as ox
        - Pastikan self.graph sudah dimuat (raise RuntimeError jika belum)
        - Return ox.nearest_nodes(self.graph, lon, lat)
          (Perhatian: osmnx menerima (X=lon, Y=lat), bukan (lat, lon)!)
        """
        pass

    def compute_distance_matrix(self, problem: VRPProblem) -> list:
        """
        Hitung matriks jarak jalan nyata antar semua node dalam VRPProblem.

        Node index di matriks: 0 = depot, 1..n = delivery nodes
        (urutan sesuai problem.get_all_nodes())

        Return:
          list[list[float]]: matriks n×n berisi jarak dalam meter

        TODO:
        - Pastikan self.graph sudah dimuat
        - Snap semua node ke graf OSM (panggil snap_to_graph untuk setiap node)
          dan simpan osm_node_id ke masing-masing DeliveryNode
        - Buat matriks n×n dengan numpy zeros
        - Untuk setiap pasang (i, j) dengan i != j:
            Panggil self._get_path_length(osm_id_i, osm_id_j)
        - Simpan ke problem.dist_matrix
        - Return matriks tersebut
        """
        pass

    def _get_path_length(self, node_a: int, node_b: int) -> float:
        """
        Hitung jarak jalan terpendek antara dua node OSM.

        Parameter:
          node_a, node_b: ID node OSM

        Return:
          float: Jarak dalam meter

        TODO:
        - import networkx as nx
        - Coba: nx.shortest_path_length(self.graph, node_a, node_b, weight='length')
        - Jika NetworkXNoPath atau NodeNotFound:
            Gunakan fallback Euclidean antar koordinat node tersebut
            (ambil koordinat dari self.graph.nodes[node_a])
        """
        pass

    def _euclidean_fallback(self, node_a: int, node_b: int) -> float:
        """
        Hitung jarak Euclidean (garis lurus) sebagai fallback.
        Menggunakan rumus Haversine untuk akurasi pada koordinat geografis.

        TODO:
        - Ambil lat/lon node_a dari self.graph.nodes[node_a]['y'/'x']
        - Ambil lat/lon node_b dari self.graph.nodes[node_b]['y'/'x']
        - Hitung dengan rumus Haversine
        - Return jarak dalam meter
        Rumus referensi: https://en.wikipedia.org/wiki/Haversine_formula
        """
        pass
