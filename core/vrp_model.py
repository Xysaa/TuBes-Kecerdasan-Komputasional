"""
core/vrp_model.py — Model Data VRP
====================================
Berisi kelas-kelas data yang merepresentasikan:
  - DeliveryNode  : satu titik lokasi pengiriman
  - Vehicle       : satu kendaraan pengantar
  - VRPProblem    : keseluruhan masalah VRP (depot + semua node + kendaraan)

PIC:  Jefri Wahyu Fernando Sembiring
"""


class DeliveryNode:
    """
    Merepresentasikan satu titik lokasi pengiriman beserta seluruh atribut paketnya.
    """

    def __init__(self, node_id, name, lat, lon, weight_kg=0.0, deadline_h=24.0):
        # Menyimpan parameter identitas unik dan data geografis node
        self.node_id = node_id
        self.name = name
        self.lat = lat
        self.lon = lon
        
        # Atribut paket: berat (kg) dan batas waktu sisa pengiriman (jam)
        self.weight_kg = weight_kg
        self.deadline_h = deadline_h
        
        # ID node pada graf OpenStreetMap, akan diisi oleh OSMHandler saat penentuan titik terdekat
        self.osm_node_id = None
        
        # Skor prioritas (skala 0.0 - 100.0), akan dikalkulasi dan diisi oleh FuzzyEvaluator
        self.priority = 0.0

    def __repr__(self):
        # Mengembalikan representasi string terformat untuk mempermudah proses debugging
        return f"DeliveryNode(id={self.node_id}, name='{self.name}', priority={self.priority:.1f})"


class Vehicle:
    """
    Merepresentasikan satu armada kendaraan pengiriman beserta kapasitas maksimalnya.
    """

    def __init__(self, vehicle_id, capacity_kg=100.0):
        # Menyimpan ID unik kendaraan dan batas maksimal kapasitas muatan
        self.vehicle_id = vehicle_id
        self.capacity_kg = capacity_kg
        
        # Menyimpan urutan node_id dari lokasi-lokasi yang dikunjungi dalam rute saat ini
        self.route = []
        
        # Akumulasi total jarak tempuh rute kendaraan ini dalam satuan meter
        self.total_distance = 0.0

    def reset_route(self):
        # Mengosongkan daftar kunjungan rute sebelum memulai iterasi koloni semut yang baru
        self.route = []
        # Mengembalikan akumulasi jarak tempuh ke angka nol
        self.total_distance = 0.0

    def current_load(self, nodes: dict) -> float:
        """
        Menghitung total berat paket yang sedang diangkut di dalam rute kendaraan saat ini.

        Parameter:
          nodes (dict): Kamus data berformat {node_id: DeliveryNode}
        """
        total_weight = 0.0
        
        # Iterasi setiap kode node_id yang telah dimasukkan ke dalam rute kendaraan
        for node_id in self.route:
            # Mengambil objek DeliveryNode dari kamus data berdasarkan node_id
            if node_id in nodes:
                # Menambahkan berat paket node tersebut ke akumulasi total
                total_weight += nodes[node_id].weight_kg
                
        return total_weight


class VRPProblem:
    """
    Merepresentasikan model utuh dari permasalahan Vehicle Routing Problem (VRP).
    """

    def __init__(self, depot: DeliveryNode, nodes: list, vehicles: list):
        # Menyimpan titik awal/akhir (depot), daftar node tujuan, dan daftar kendaraan
        self.depot = depot
        self.nodes = nodes
        self.vehicles = vehicles
        
        # Matriks jarak berdimensi n x n (dalam meter) yang nantinya dihitung oleh OSMHandler
        # Indeks 0 merepresentasikan depot, sedangkan indeks 1 hingga n melambangkan delivery nodes
        self.dist_matrix = None

    def get_all_nodes(self) -> list:
        # Menggabungkan titik depot di awal list diikuti oleh seluruh node tujuan pengiriman
        return [self.depot] + self.nodes

    def validate(self) -> bool:
        """
        Validasi kesiapan data masalah sebelum dieksekusi oleh algoritma optimasi ACO.
        """
        # Memastikan bahwa objek lokasi depot telah diatur dan tidak bernilai None
        if self.depot is None:
            return False
            
        # Memastikan daftar lokasi pengantaran paket tidak dalam keadaan kosong
        if not self.nodes:
            return False
            
        # Memastikan tersedianya armada kendaraan untuk melakukan pengiriman
        if not self.vehicles:
            return False
            
        # Memastikan matriks jarak riil jalan raya telah dihitung dan siap digunakan
        if self.dist_matrix is None:
            return False
            
        # Jika seluruh kondisi terpenuhi, struktur problem dinyatakan valid dan siap dijalankan
        return True