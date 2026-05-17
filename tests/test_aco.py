"""
tests/test_aco.py — Unit Test Algoritma ACO
=============================================
Test seluruh fungsionalitas ACOSolver menggunakan data dummy
(tanpa koneksi internet / OSM).

PIC: Jefri (QA & Integrasi)
"""

import pytest
import numpy as np
from core.aco import ACOSolver
from core.vrp_model import VRPProblem, DeliveryNode, Vehicle


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_dist_matrix(n: int, base: float = 1000.0) -> list:
    """
    Buat matriks jarak dummy n×n.
    Jarak antar node = base * |i - j|, diagonal = 0.
    """
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = base * abs(i - j)
    return matrix


def make_problem(n_delivery: int = 3,
                 n_vehicles: int = 1,
                 capacity: float = 100.0,
                 weight_per_node: float = 10.0) -> VRPProblem:
    """
    Helper: buat VRPProblem lengkap siap pakai dengan data dummy.

    Parameter:
      n_delivery      : jumlah delivery node (tidak termasuk depot)
      n_vehicles      : jumlah kendaraan
      capacity        : kapasitas tiap kendaraan (kg)
      weight_per_node : berat paket tiap node (kg)
    """
    depot = DeliveryNode(0, "Depot", -5.39, 105.26,
                         weight_kg=0.0, deadline_h=99.0)

    nodes = [
        DeliveryNode(i + 1, f"Node-{i+1}",
                     -5.39 + i * 0.01, 105.26 + i * 0.01,
                     weight_kg=weight_per_node,
                     deadline_h=12.0)
        for i in range(n_delivery)
    ]

    vehicles = [Vehicle(v + 1, capacity_kg=capacity) for v in range(n_vehicles)]

    problem = VRPProblem(depot, nodes, vehicles)
    problem.dist_matrix = make_dist_matrix(n_delivery + 1)  # +1 untuk depot
    return problem


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def simple_problem():
    """VRPProblem dengan 3 delivery node, 1 kendaraan, kapasitas 100 kg."""
    return make_problem(n_delivery=3, n_vehicles=1, capacity=100.0)


@pytest.fixture
def aco_solver(simple_problem):
    """ACOSolver dengan parameter kecil agar test cepat."""
    return ACOSolver(simple_problem, n_ants=5, n_iterations=10)


# ── Tests Inisialisasi ────────────────────────────────────────────────────────

def test_solver_initialization(aco_solver):
    """State awal solver harus kosong sebelum solve() dipanggil."""
    assert aco_solver.best_distance == float('inf')
    assert aco_solver.best_solution is None
    assert aco_solver.convergence_history == []


def test_pheromone_init_shape(aco_solver, simple_problem):
    """Matriks feromon harus berukuran n×n dan semua nilainya > 0 (kecuali diagonal)."""
    aco_solver._init_pheromone()

    n_nodes = len(simple_problem.get_all_nodes())  # depot + 3 node = 4
    assert aco_solver.pheromone.shape == (n_nodes, n_nodes)

    # Semua nilai non-diagonal harus > 0
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j:
                assert aco_solver.pheromone[i][j] > 0, (
                    f"Feromon[{i}][{j}] seharusnya > 0, dapat: {aco_solver.pheromone[i][j]}"
                )


def test_pheromone_diagonal_zero(aco_solver):
    """Diagonal matriks feromon harus 0 (semut tidak ke node yang sama)."""
    aco_solver._init_pheromone()
    n = aco_solver.pheromone.shape[0]
    for i in range(n):
        assert aco_solver.pheromone[i][i] == 0.0


# ── Tests Solve ───────────────────────────────────────────────────────────────

def test_solve_returns_valid_structure(aco_solver):
    """solve() harus return dict dengan key 'routes', 'distance', 'history'."""
    solution = aco_solver.solve()

    assert 'routes'   in solution, "Key 'routes' tidak ada di hasil solve()"
    assert 'distance' in solution, "Key 'distance' tidak ada di hasil solve()"
    assert 'history'  in solution, "Key 'history' tidak ada di hasil solve()"

    assert solution['distance'] > 0, "Total jarak harus > 0"
    assert len(solution['history']) == aco_solver.n_iterations, (
        f"Panjang history seharusnya {aco_solver.n_iterations}, "
        f"dapat: {len(solution['history'])}"
    )


def test_solve_visits_all_nodes(aco_solver, simple_problem):
    """Semua delivery node harus dikunjungi tepat sekali."""
    solution = aco_solver.solve()

    # Kumpulkan semua index node dari semua rute
    visited = []
    for route in solution['routes']:
        visited.extend(route)

    n_delivery = len(simple_problem.nodes)
    expected   = set(range(1, n_delivery + 1))  # index 1..n (bukan 0/depot)

    assert set(visited) == expected, (
        f"Node yang dikunjungi: {sorted(visited)}, seharusnya: {sorted(expected)}"
    )


def test_solve_no_duplicate_visits(aco_solver, simple_problem):
    """Tidak boleh ada node yang dikunjungi lebih dari satu kali."""
    solution = aco_solver.solve()

    visited = []
    for route in solution['routes']:
        visited.extend(route)

    assert len(visited) == len(set(visited)), (
        f"Ada node yang dikunjungi lebih dari sekali: {visited}"
    )


def test_convergence_history_decreasing(aco_solver):
    """Best distance di akhir tidak boleh lebih buruk dari iterasi pertama."""
    solution = aco_solver.solve()
    history  = solution['history']

    assert history[-1] <= history[0], (
        f"Konvergensi tidak terjadi: awal={history[0]:.1f}, akhir={history[-1]:.1f}"
    )


def test_callback_called_correct_times(simple_problem):
    """Callback harus dipanggil tepat n_iterations kali."""
    n_iter   = 10
    solver   = ACOSolver(simple_problem, n_ants=3, n_iterations=n_iter)
    counter  = {'count': 0}

    def dummy_callback(iteration, best_dist):
        counter['count'] += 1

    solver.solve(callback=dummy_callback)
    assert counter['count'] == n_iter, (
        f"Callback dipanggil {counter['count']} kali, seharusnya {n_iter}"
    )


# ── Tests Edge Cases ──────────────────────────────────────────────────────────

def test_single_node_problem():
    """ACO dengan hanya 1 delivery node harus berjalan tanpa error."""
    problem  = make_problem(n_delivery=1, n_vehicles=1, capacity=100.0)
    solver   = ACOSolver(problem, n_ants=3, n_iterations=5)
    solution = solver.solve()

    visited = [node for route in solution['routes'] for node in route]
    assert 1 in visited, "Node 1 (satu-satunya delivery node) harus dikunjungi"


def test_multiple_vehicles(simple_problem):
    """Dengan 2 kendaraan, tidak boleh ada node yang dikunjungi lebih dari sekali."""
    # Tambah kendaraan kedua
    simple_problem.vehicles.append(Vehicle(2, capacity_kg=100.0))

    solver   = ACOSolver(simple_problem, n_ants=5, n_iterations=10)
    solution = solver.solve()

    visited = []
    for route in solution['routes']:
        visited.extend(route)

    assert len(visited) == len(set(visited)), (
        f"Ada duplikasi kunjungan dengan 2 kendaraan: {visited}"
    )


def test_priority_bias():
    """
    Node prioritas tinggi (90) seharusnya lebih sering muncul di posisi
    pertama rute dibanding node prioritas rendah (10),
    ketika jarak keduanya sama dari depot.
    """
    # Buat problem dengan 2 node, jarak ke keduanya sama dari depot
    depot  = DeliveryNode(0, "Depot", -5.39, 105.26, weight_kg=0.0, deadline_h=99.0)
    node_hi = DeliveryNode(1, "High",  -5.40, 105.27, weight_kg=5.0, deadline_h=12.0)
    node_lo = DeliveryNode(2, "Low",   -5.41, 105.28, weight_kg=5.0, deadline_h=12.0)

    node_hi.priority = 90.0  # prioritas tinggi
    node_lo.priority = 10.0  # prioritas rendah

    vehicles = [Vehicle(1, capacity_kg=100.0)]
    problem  = VRPProblem(depot, [node_hi, node_lo], vehicles)

    # Jarak depot → node_hi == depot → node_lo (sama persis)
    problem.dist_matrix = [
        [0,    1000, 1000],
        [1000,    0, 1000],
        [1000, 1000,    0],
    ]

    # Jalankan banyak kali dan hitung seberapa sering node_hi duluan
    n_runs    = 30
    hi_first  = 0

    for _ in range(n_runs):
        solver   = ACOSolver(problem, n_ants=10, n_iterations=50)
        solution = solver.solve()

        # Ambil rute pertama yang tidak kosong
        for route in solution['routes']:
            if route:
                if route[0] == 1:  # index 1 = node_hi
                    hi_first += 1
                break

    # Node prioritas tinggi harus muncul duluan lebih dari 50% dari percobaan
    assert hi_first > n_runs * 0.5, (
        f"Node prioritas tinggi hanya muncul pertama {hi_first}/{n_runs} kali "
        f"(seharusnya > {n_runs * 0.5:.0f})"
    )