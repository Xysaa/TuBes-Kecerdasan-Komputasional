"""
tests/test_fuzzy.py — Unit Test Fuzzy Logic Evaluator
=======================================================
Test FuzzyEvaluator untuk memastikan output skor
konsisten dengan logika rule yang sudah didefinisikan.

PIC: Jefri (QA & Integrasi)
Kolaborasi: Annisa (verifikasi rule logic)
"""

import pytest
from core.fuzzy_evaluator import FuzzyEvaluator
from core.vrp_model import DeliveryNode


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def evaluator():
    """
    Buat satu instance FuzzyEvaluator yang dipakai bersama semua test.
    scope="module" supaya FIS hanya dibangun sekali — lebih cepat.
    """
    return FuzzyEvaluator()


def make_node(node_id, weight_kg, deadline_h) -> DeliveryNode:
    """Helper: buat DeliveryNode sederhana untuk testing."""
    return DeliveryNode(node_id, f"Node-{node_id}", -5.39, 105.26,
                        weight_kg=weight_kg, deadline_h=deadline_h)


# ── Tests Output Range ────────────────────────────────────────────────────────

def test_output_in_valid_range(evaluator):
    """Semua kombinasi input harus menghasilkan output dalam rentang [0, 100]."""
    test_cases = [
        (2,  10, 5),   # mendesak, ringan, dekat
        (12, 25, 25),  # normal, sedang, sedang
        (22, 2,  5),   # santai, ringan, dekat
        (1,  48, 48),  # mendesak, berat, jauh
        (20, 40, 40),  # santai, berat, jauh
    ]
    for deadline_h, weight_kg, jarak_km in test_cases:
        node  = make_node(1, weight_kg, deadline_h)
        score = evaluator.evaluate(node, jarak_km)
        assert 0.0 <= score <= 100.0, (
            f"Skor {score} di luar range untuk "
            f"deadline={deadline_h}, berat={weight_kg}, jarak={jarak_km}"
        )


# ── Tests Logika Rule ─────────────────────────────────────────────────────────

def test_urgent_deadline_gives_high_priority(evaluator):
    """Node dengan deadline mendesak (2 jam) harus mendapat prioritas tinggi (>= 67)."""
    node  = make_node(1, weight_kg=10, deadline_h=2)
    score = evaluator.evaluate(node, distance_from_depot_km=5)
    assert score >= 67, f"Deadline mendesak seharusnya prioritas tinggi, dapat: {score:.1f}"


def test_relaxed_light_package_gives_low_priority(evaluator):
    """Node dengan deadline santai (22 jam) dan paket ringan harus prioritas rendah (< 34)."""
    node  = make_node(2, weight_kg=2, deadline_h=22)
    score = evaluator.evaluate(node, distance_from_depot_km=5)
    assert score < 34, f"Deadline santai + ringan seharusnya prioritas rendah, dapat: {score:.1f}"


def test_far_node_increases_priority(evaluator):
    """Jarak lebih jauh harus meningkatkan skor prioritas (input lain sama)."""
    node_dekat = make_node(1, weight_kg=15, deadline_h=12)
    node_jauh  = make_node(2, weight_kg=15, deadline_h=12)

    skor_dekat = evaluator.evaluate(node_dekat, distance_from_depot_km=5)
    skor_jauh  = evaluator.evaluate(node_jauh,  distance_from_depot_km=45)

    assert skor_jauh >= skor_dekat, (
        f"Node jauh ({skor_jauh:.1f}) seharusnya >= node dekat ({skor_dekat:.1f})"
    )


def test_heavy_urgent_package_highest_priority(evaluator):
    """Kombinasi mendesak + berat + jauh harus menghasilkan skor sangat tinggi (> 80)."""
    node  = make_node(1, weight_kg=48, deadline_h=1)
    score = evaluator.evaluate(node, distance_from_depot_km=48)
    assert score > 80, f"Kombinasi terburuk seharusnya > 80, dapat: {score:.1f}"


# ── Tests Evaluate All ────────────────────────────────────────────────────────

def test_evaluate_all_fills_priority(evaluator):
    """Setelah evaluate_all(), setiap node.priority harus terisi (bukan 0.0)."""
    nodes = [
        make_node(1, weight_kg=10, deadline_h=3),
        make_node(2, weight_kg=25, deadline_h=12),
        make_node(3, weight_kg=5,  deadline_h=22),
    ]
    # dist_matrix 4×4: index 0 = depot, 1-3 = nodes (dalam meter)
    dist_matrix = [
        [0,    5000,  15000, 25000],
        [5000,    0,  10000, 20000],
        [15000, 10000,    0, 10000],
        [25000, 20000, 10000,    0],
    ]
    evaluator.evaluate_all(nodes, dist_matrix, depot_index=0)

    for node in nodes:
        assert node.priority != 0.0, (
            f"Node {node.node_id} priority belum terisi (masih 0.0)"
        )
        assert 0.0 <= node.priority <= 100.0


def test_evaluate_all_returns_correct_length(evaluator):
    """evaluate_all() harus return list dengan panjang sama dengan jumlah node."""
    nodes = [make_node(i, weight_kg=10 * i, deadline_h=24 - i) for i in range(1, 6)]

    # dist_matrix 6×6 (depot + 5 node)
    dist_matrix = [[abs(i - j) * 3000 for j in range(6)] for i in range(6)]

    scores = evaluator.evaluate_all(nodes, dist_matrix, depot_index=0)

    assert len(scores) == 5, f"Panjang scores seharusnya 5, dapat: {len(scores)}"


# ── Tests Priority Label ──────────────────────────────────────────────────────

def test_priority_label_mapping(evaluator):
    """get_priority_label() harus return label yang sesuai untuk setiap rentang skor."""
    assert "Rendah" in evaluator.get_priority_label(20),  "Skor 20 → Rendah"
    assert "Sedang" in evaluator.get_priority_label(50),  "Skor 50 → Sedang"
    assert "Tinggi" in evaluator.get_priority_label(80),  "Skor 80 → Tinggi"
    assert "Rendah" in evaluator.get_priority_label(33),  "Skor 33 → batas atas Rendah"
    assert "Tinggi" in evaluator.get_priority_label(67),  "Skor 67 → batas bawah Tinggi"