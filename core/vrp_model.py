"""
core/vrp_model.py — Model Data VRP
====================================
Berisi kelas-kelas data yang merepresentasikan:
  - DeliveryNode  : satu titik lokasi pengiriman
  - Vehicle       : satu kendaraan pengantar
  - VRPProblem    : keseluruhan masalah VRP (depot + semua node + kendaraan)

PIC: Anggota 1 (ACO Engineer)
"""


class DeliveryNode:
    """
    Merepresentasikan satu titik lokasi pengiriman.

    Atribut yang perlu ada:
      - node_id     (int)   : ID unik node
      - name        (str)   : Nama lokasi (misal: "Pasar Tengah")
      - lat         (float) : Latitude koordinat
      - lon         (float) : Longitude koordinat
      - osm_node_id (int)   : ID node di graf OSM (hasil nearest_nodes)
      - weight_kg   (float) : Berat paket dalam kilogram
      - deadline_h  (float) : Sisa waktu deadline dalam jam
      - priority    (float) : Skor prioritas (0-100), diisi oleh FuzzyEvaluator

    TODO:
    - Implementasi __init__ dengan parameter di atas
    - Implementasi __repr__ untuk debugging yang informatif
    """

    def __init__(self, node_id, name, lat, lon, weight_kg=0.0, deadline_h=24.0):
        """
        TODO:
        - Simpan semua parameter ke self
        - Set osm_node_id = None (akan diisi oleh OSMHandler)
        - Set priority = 0.0 (akan diisi oleh FuzzyEvaluator)
        """
        pass

    def __repr__(self):
        """
        TODO:
        - Return string informatif, contoh:
          "DeliveryNode(id=1, name='Pasar Tengah', priority=85.0)"
        """
        pass


class Vehicle:
    """
    Merepresentasikan satu kendaraan pengiriman.

    Atribut yang perlu ada:
      - vehicle_id      (int)         : ID unik kendaraan
      - capacity_kg     (float)       : Kapasitas muatan maksimum (kg)
      - route           (list[int])   : Daftar node_id yang dikunjungi (urutan)
      - total_distance  (float)       : Total jarak rute dalam meter

    TODO:
    - Implementasi __init__
    - Implementasi reset_route() untuk mengosongkan rute
    - Implementasi current_load() untuk menghitung total berat paket saat ini
    """

    def __init__(self, vehicle_id, capacity_kg=100.0):
        """
        TODO:
        - Simpan vehicle_id dan capacity_kg
        - Inisialisasi route sebagai list kosong
        - Inisialisasi total_distance = 0.0
        """
        pass

    def reset_route(self):
        """
        TODO:
        - Kosongkan self.route menjadi []
        - Reset self.total_distance menjadi 0.0
        """
        pass

    def current_load(self, nodes: dict) -> float:
        """
        Hitung total berat paket yang sudah ada di rute kendaraan ini.

        Parameter:
          nodes (dict): dict {node_id: DeliveryNode}

        TODO:
        - Iterasi self.route
        - Jumlahkan weight_kg dari setiap node yang ada di route
        - Return total berat (float)
        """
        pass


class VRPProblem:
    """
    Merepresentasikan keseluruhan masalah VRP.

    Atribut yang perlu ada:
      - depot       (DeliveryNode)       : Titik awal & akhir semua kendaraan
      - nodes       (list[DeliveryNode]) : Semua titik pengiriman (tidak termasuk depot)
      - vehicles    (list[Vehicle])      : Daftar kendaraan yang tersedia
      - dist_matrix (list[list[float]])  : Matriks jarak antar node (meter)
        Index 0 = depot, index 1..n = nodes

    TODO:
    - Implementasi __init__(depot, nodes, vehicles)
    - Implementasi get_all_nodes() yang return [depot] + nodes
    - Implementasi validate() yang return True jika data lengkap dan valid
    """

    def __init__(self, depot: DeliveryNode, nodes: list, vehicles: list):
        """
        TODO:
        - Simpan depot, nodes, vehicles ke self
        - Inisialisasi dist_matrix sebagai None (diisi oleh OSMHandler)
        """
        pass

    def get_all_nodes(self) -> list:
        """
        TODO:
        - Return list gabungan: [self.depot] + self.nodes
        """
        pass

    def validate(self) -> bool:
        """
        Validasi bahwa problem sudah siap dijalankan ACO.

        TODO:
        - Cek depot tidak None
        - Cek nodes tidak kosong
        - Cek vehicles tidak kosong
        - Cek dist_matrix sudah terisi (tidak None)
        - Return True jika semua valid, False jika ada yang kurang
        """
        pass
