"""
core/aco.py — Algoritma Ant Colony Optimization
=================================================
Implementasi ACO untuk menyelesaikan Vehicle Routing Problem (VRP).

Alur kerja ACO:
  1. Inisialisasi matriks feromon (nilai awal seragam)
  2. Setiap iterasi: semua semut membangun solusi rute
  3. Evaluasi total jarak setiap solusi
  4. Update feromon: evaporasi + penguatan jalur terbaik
  5. Simpan solusi terbaik (global best)
  6. Ulangi hingga iterasi selesai

Referensi:
  Dorigo, M., & Stützle, T. (2004). Ant Colony Optimization. MIT Press.

PIC: Stevanus (ACO Engineer)
Kolaborasi: Annisa (integrasi skor Fuzzy ke heuristik)
"""

import numpy as np
import random
from core.vrp_model import VRPProblem


class ACOSolver:
    """
    Solver ACO untuk VRP.

    Parameter ACO:
      - n_ants      : Jumlah semut per iterasi (rekomendasi: 20-50)
      - n_iterations: Jumlah iterasi total (rekomendasi: 100-500)
      - alpha       : Bobot feromon (rekomendasi: 1.0)
      - beta        : Bobot heuristik jarak (rekomendasi: 2.0-5.0)
      - rho         : Laju evaporasi feromon (rekomendasi: 0.1-0.5)
      - Q           : Konstanta penguatan feromon (rekomendasi: 100.0)
    """

    def __init__(self, problem: VRPProblem,
                 n_ants=30, n_iterations=200,
                 alpha=1.0, beta=3.0, rho=0.3, Q=100.0):
        self.problem        = problem
        self.n_ants         = n_ants
        self.n_iterations   = n_iterations
        self.alpha          = alpha
        self.beta           = beta
        self.rho            = rho
        self.Q              = Q

        self.pheromone          = None
        self.best_solution      = None
        self.best_distance      = float('inf')
        self.convergence_history = []

    # ── Public ────────────────────────────────────────────────────────────────

    def solve(self, callback=None) -> dict:
        """
        Jalankan algoritma ACO dan return solusi terbaik.

        Parameter:
          callback (callable): Dipanggil setiap iterasi selesai.
                               Signature: callback(iteration, best_distance)

        Return:
          dict dengan key:
            'routes'   : list[list[int]] — rute per kendaraan (node_id)
            'distance' : float           — total jarak terbaik (meter)
            'history'  : list[float]     — riwayat best distance per iterasi
        """
        self._init_pheromone()
        self.convergence_history = []
        self.best_solution = None
        self.best_distance = float('inf')

        for iteration in range(self.n_iterations):
            # a. Bangun solusi semua semut
            solutions = self._build_solutions()

            # b & c. Evaluasi jarak setiap solusi + update best
            for sol in solutions:
                dist = self._evaluate_solution(sol)
                sol['distance'] = dist
                if dist < self.best_distance:
                    self.best_distance = dist
                    self.best_solution = sol

            # d. Update feromon
            self._update_pheromone(solutions)

            # e. Catat konvergensi
            self.convergence_history.append(self.best_distance)

            # f. Callback GUI (progress bar)
            if callback is not None:
                callback(iteration + 1, self.best_distance)

        return {
            'routes'  : self.best_solution['routes'],
            'distance': self.best_distance,
            'history' : self.convergence_history,
        }

    # ── Private ───────────────────────────────────────────────────────────────

    def _init_pheromone(self):
        """Inisialisasi matriks feromon dengan nilai seragam kecil."""
        n = len(self.problem.get_all_nodes())  # depot + delivery nodes
        initial_value = 1.0 / n
        self.pheromone = np.full((n, n), initial_value, dtype=float)
        np.fill_diagonal(self.pheromone, 0.0)  # diagonal = 0 (tidak ke diri sendiri)

    def _build_solutions(self) -> list:
        """Bangun solusi untuk semua semut dalam satu iterasi."""
        return [self._build_single_ant_solution() for _ in range(self.n_ants)]

    def _build_single_ant_solution(self) -> dict:
        """
        Satu semut membangun solusi rute untuk semua kendaraan.

        Strategi distribusi: node dibagi terlebih dahulu secara proporsional
        ke setiap kendaraan (target_load = total_weight / n_vehicles) agar
        beban tersebar merata. Kendaraan berhenti mengambil node baru saat
        sudah mendekati target beban, kecuali masih ada sisa node.

        Index node di dist_matrix: 0 = depot, 1..n = delivery nodes.
        """
        all_nodes   = self.problem.get_all_nodes()
        n_delivery  = len(self.problem.nodes)
        n_vehicles  = len(self.problem.vehicles)

        unvisited   = list(range(1, n_delivery + 1))
        random.shuffle(unvisited)

        # Hitung target beban per kendaraan untuk distribusi merata
        total_weight  = sum(all_nodes[i].weight_kg for i in unvisited)
        target_load   = total_weight / n_vehicles  # beban ideal per kendaraan

        routes = []

        for v_idx, vehicle in enumerate(self.problem.vehicles):
            if not unvisited:
                routes.append([])
                continue

            route        = []
            current      = 0
            vehicle_load = 0.0

            # Kendaraan terakhir: ambil semua sisa node tanpa batasan target
            is_last_vehicle = (v_idx == n_vehicles - 1)

            while unvisited:
                # Jika sudah mendekati target DAN bukan kendaraan terakhir,
                # berhenti agar kendaraan berikutnya mendapat jatah yang cukup
                remaining_vehicles = n_vehicles - v_idx - 1
                if (not is_last_vehicle
                        and remaining_vehicles > 0
                        and vehicle_load >= target_load):
                    # Cek apakah kendaraan berikutnya masih bisa menampung sisa
                    remaining_weight = sum(all_nodes[i].weight_kg for i in unvisited)
                    if remaining_weight <= remaining_vehicles * vehicle.capacity_kg:
                        break  # kendaraan ini sudah cukup, beri giliran berikutnya

                next_node = self._select_next_node(
                    current, unvisited, vehicle_load, vehicle.capacity_kg
                )
                if next_node == -1:
                    break  # kapasitas penuh

                route.append(next_node)
                unvisited.remove(next_node)

                node_obj      = all_nodes[next_node]
                vehicle_load += node_obj.weight_kg
                current       = next_node

            routes.append(route)

        # Fallback: sisa node yang belum terkunjungi → kendaraan terakhir
        if unvisited and routes:
            routes[-1].extend(unvisited)

        return {'routes': routes, 'distance': 0.0}

    def _select_next_node(self, current_node: int, unvisited: list,
                          vehicle_load: float, capacity: float) -> int:
        """
        Pilih node berikutnya menggunakan probabilitas ACO.

        Heuristik dimodifikasi dengan skor prioritas Fuzzy:
          eta[i][j] = (1 / jarak[i][j]) * (1 + priority[j] / 100)

        Return:
          int: index node terpilih, atau -1 jika tidak ada kandidat valid.
        """
        all_nodes  = self.problem.get_all_nodes()
        dist_matrix = self.problem.dist_matrix

        # Filter: hanya node yang kapasitasnya masih muat
        kandidat = [
            j for j in unvisited
            if vehicle_load + all_nodes[j].weight_kg <= capacity
        ]

        if not kandidat:
            return -1

        # Hitung numerator probabilitas setiap kandidat
        weights = []
        for j in kandidat:
            jarak = dist_matrix[current_node][j]
            if jarak <= 0:
                jarak = 1e-9  # hindari pembagian nol

            priority = getattr(all_nodes[j], 'priority', 0.0)
            eta      = (1.0 / jarak) * (1.0 + priority / 100.0)
            tau      = self.pheromone[current_node][j]

            w = (tau ** self.alpha) * (eta ** self.beta)
            weights.append(max(w, 1e-10))  # pastikan weight selalu positif

        # Pilih secara probabilistik
        chosen = random.choices(kandidat, weights=weights, k=1)[0]
        return chosen

    def _evaluate_solution(self, solution: dict) -> float:
        """
        Hitung total jarak semua rute dalam satu solusi.

        Setiap rute: depot(0) → node_a → node_b → ... → depot(0)
        """
        dist_matrix  = self.problem.dist_matrix
        total_distance = 0.0

        for route in solution['routes']:
            if not route:
                continue

            # depot → node pertama
            total_distance += dist_matrix[0][route[0]]

            # antar node
            for k in range(len(route) - 1):
                total_distance += dist_matrix[route[k]][route[k + 1]]

            # node terakhir → depot
            total_distance += dist_matrix[route[-1]][0]

        return total_distance

    def _update_pheromone(self, solutions: list):
        """
        Update matriks feromon: evaporasi + penguatan dari semua semut.

        Rumus:
          tau[i][j] = (1 - rho) * tau[i][j]          ← evaporasi
          tau[i][j] += Q / distance  (tiap semut)     ← penguatan
        """
        # Evaporasi
        self.pheromone *= (1.0 - self.rho)

        # Penguatan dari setiap solusi semut
        for sol in solutions:
            if sol['distance'] <= 0:
                continue

            delta = self.Q / sol['distance']

            for route in sol['routes']:
                if not route:
                    continue

                # Edge: depot → node pertama
                self.pheromone[0][route[0]]      += delta
                self.pheromone[route[0]][0]      += delta

                # Edge: antar node dalam rute
                for k in range(len(route) - 1):
                    i, j = route[k], route[k + 1]
                    self.pheromone[i][j] += delta
                    self.pheromone[j][i] += delta

                # Edge: node terakhir → depot
                self.pheromone[route[-1]][0]     += delta
                self.pheromone[0][route[-1]]     += delta

        # Clip agar feromon tidak drop terlalu rendah
        np.clip(self.pheromone, 1e-10, None, out=self.pheromone)
        np.fill_diagonal(self.pheromone, 0.0)