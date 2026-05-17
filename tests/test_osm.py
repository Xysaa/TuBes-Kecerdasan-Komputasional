"""
tests/test_osm.py — Unit Test OSM Handler
==========================================
Test OSMHandler dengan mock agar tidak perlu koneksi internet.
Menggunakan unittest.mock untuk mensimulasikan OSMnx dan Geopy.

PIC: Anggota 5 (QA & Integrasi)
Kolaborasi: Anggota 4 (verifikasi logika handler)
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from geopy.exc import GeocoderTimedOut

from data.osm_handler import OSMHandler, _haversine
from core.vrp_model import DeliveryNode, Vehicle, VRPProblem


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def handler():
    """OSMHandler yang diarahkan ke cache sementara agar tidak menyentuh disk nyata."""
    return OSMHandler(city="Test City", cache_file="/tmp/test_graph.graphml")


@pytest.fixture
def simple_problem():
    """VRPProblem minimal: 1 depot + 2 delivery node + 1 kendaraan."""
    depot = DeliveryNode(node_id=0, name="Depot", lat=-5.39, lon=105.26)
    node1 = DeliveryNode(node_id=1, name="Lokasi A", lat=-5.40, lon=105.27,
                         weight_kg=5.0, deadline_h=12.0)
    node2 = DeliveryNode(node_id=2, name="Lokasi B", lat=-5.41, lon=105.28,
                         weight_kg=3.0, deadline_h=8.0)
    vehicle = Vehicle(vehicle_id=1, capacity_kg=100.0)
    return VRPProblem(depot=depot, nodes=[node1, node2], vehicles=[vehicle])


# ── Tests Geocoding ───────────────────────────────────────────────────────────

def test_geocode_success(handler):
    """Geocoding berhasil → return tuple (lat, lon) yang benar."""
    mock_location = MagicMock()
    mock_location.latitude = -5.3971
    mock_location.longitude = 105.2668

    with patch.object(handler.geolocator, "geocode", return_value=mock_location):
        lat, lon = handler.geocode("Pasar Tengah, Bandar Lampung")

    assert lat == pytest.approx(-5.3971)
    assert lon == pytest.approx(105.2668)


def test_geocode_not_found_returns_none(handler):
    """Geocoder tidak menemukan lokasi → return (None, None)."""
    with patch.object(handler.geolocator, "geocode", return_value=None):
        result = handler.geocode("Tempat Tidak Ada XYZ")

    assert result == (None, None)


def test_geocode_timeout_handled(handler):
    """Geocoder timeout → tidak crash, return (None, None)."""
    with patch.object(handler.geolocator, "geocode",
                      side_effect=GeocoderTimedOut):
        result = handler.geocode("Pasar Tengah, Bandar Lampung")

    assert result == (None, None)


# ── Tests Graph Loading ───────────────────────────────────────────────────────

def test_load_from_cache_when_exists(handler, tmp_path):
    """
    Jika file cache ada dan force_download=False, graf harus dimuat dari cache
    (bukan diunduh ulang).
    """
    # Buat file dummy agar os.path.exists() → True
    cache_path = tmp_path / "test_graph.graphml"
    cache_path.write_text("<graphml/>")
    handler.cache_file = str(cache_path)

    mock_graph = MagicMock()

    with patch("data.osm_handler.ox", create=True) as mock_ox, \
         patch("data.osm_handler.__import__", wraps=__builtins__["__import__"]
               if isinstance(__builtins__, dict) else __import__) as _:
        pass  # pre-flight import check; real mock below

    with patch("osmnx.load_graphml", return_value=mock_graph) as mock_load, \
         patch("osmnx.graph_from_place") as mock_download:
        handler.load_graph()

    mock_load.assert_called_once_with(str(cache_path))
    mock_download.assert_not_called()
    assert handler.graph is mock_graph


def test_download_when_no_cache(handler, tmp_path):
    """
    Jika file cache tidak ada, graf harus diunduh dari OSM.
    """
    # Pastikan cache_file mengarah ke path yang tidak ada
    handler.cache_file = str(tmp_path / "nonexistent_graph.graphml")

    mock_graph = MagicMock()

    with patch("osmnx.graph_from_place", return_value=mock_graph) as mock_dl, \
         patch("osmnx.save_graphml") as mock_save:
        handler.load_graph()

    mock_dl.assert_called_once_with("Test City", network_type="drive")
    mock_save.assert_called_once()
    assert handler.graph is mock_graph


def test_force_download_ignores_cache(handler, tmp_path):
    """
    Jika force_download=True, graf harus diunduh ulang meski cache ada.
    """
    cache_path = tmp_path / "existing_graph.graphml"
    cache_path.write_text("<graphml/>")
    handler.cache_file = str(cache_path)

    mock_graph = MagicMock()

    with patch("osmnx.graph_from_place", return_value=mock_graph) as mock_dl, \
         patch("osmnx.save_graphml") as mock_save, \
         patch("osmnx.load_graphml") as mock_load:
        handler.load_graph(force_download=True)

    mock_dl.assert_called_once_with("Test City", network_type="drive")
    mock_load.assert_not_called()
    assert handler.graph is mock_graph


# ── Tests snap_to_graph ───────────────────────────────────────────────────────

def test_snap_to_graph_raises_if_no_graph(handler):
    """snap_to_graph harus raise RuntimeError jika graf belum dimuat."""
    handler.graph = None
    with pytest.raises(RuntimeError, match="Graf belum dimuat"):
        handler.snap_to_graph(-5.39, 105.26)


def test_snap_to_graph_returns_node_id(handler):
    """snap_to_graph harus memanggil ox.nearest_nodes dengan urutan (lon, lat)."""
    handler.graph = MagicMock()
    expected_node_id = 123456789

    with patch("osmnx.nearest_nodes", return_value=expected_node_id) as mock_nn:
        result = handler.snap_to_graph(-5.39, 105.26)

    # OSMnx menerima (X=lon, Y=lat)
    mock_nn.assert_called_once_with(handler.graph, 105.26, -5.39)
    assert result == expected_node_id


# ── Tests Distance Matrix ─────────────────────────────────────────────────────

def test_distance_matrix_shape(handler, simple_problem):
    """
    Matriks hasil compute_distance_matrix harus berukuran n×n
    dan diagonal bernilai 0.
    """
    handler.graph = MagicMock()
    n = len(simple_problem.get_all_nodes())  # 3 (depot + 2 node)

    with patch.object(handler, "snap_to_graph", side_effect=[10, 20, 30]), \
         patch.object(handler, "_get_path_length", return_value=1000.0):
        matrix = handler.compute_distance_matrix(simple_problem)

    assert len(matrix) == n
    assert all(len(row) == n for row in matrix)

    # Diagonal harus nol
    for i in range(n):
        assert matrix[i][i] == pytest.approx(0.0)


def test_distance_matrix_non_diagonal_filled(handler, simple_problem):
    """Elemen non-diagonal harus terisi dengan nilai dari _get_path_length."""
    handler.graph = MagicMock()

    with patch.object(handler, "snap_to_graph", side_effect=[10, 20, 30]), \
         patch.object(handler, "_get_path_length", return_value=500.0):
        matrix = handler.compute_distance_matrix(simple_problem)

    n = len(simple_problem.get_all_nodes())
    for i in range(n):
        for j in range(n):
            if i != j:
                assert matrix[i][j] == pytest.approx(500.0)


def test_distance_matrix_stored_in_problem(handler, simple_problem):
    """compute_distance_matrix harus menyimpan hasilnya ke problem.dist_matrix."""
    handler.graph = MagicMock()

    with patch.object(handler, "snap_to_graph", side_effect=[10, 20, 30]), \
         patch.object(handler, "_get_path_length", return_value=750.0):
        matrix = handler.compute_distance_matrix(simple_problem)

    assert simple_problem.dist_matrix is matrix


def test_distance_matrix_symmetric(handler, simple_problem):
    """
    Matriks jarak harus simetris (i→j == j→i) karena _get_path_length
    dipanggil untuk setiap pasangan dan graf dianggap bidirectional.
    """
    handler.graph = MagicMock()
    call_count = [0]

    def fake_path_length(a, b):
        call_count[0] += 1
        # Kembalikan nilai yang sama untuk setiap pasangan agar simetris
        return 1000.0

    with patch.object(handler, "snap_to_graph", side_effect=[10, 20, 30]), \
         patch.object(handler, "_get_path_length", side_effect=fake_path_length):
        matrix = handler.compute_distance_matrix(simple_problem)

    n = len(simple_problem.get_all_nodes())
    for i in range(n):
        for j in range(n):
            assert matrix[i][j] == pytest.approx(matrix[j][i]), \
                f"Matriks tidak simetris pada [{i}][{j}]"


# ── Tests compute_distance_matrix raises without graph ───────────────────────

def test_distance_matrix_raises_if_no_graph(handler, simple_problem):
    """compute_distance_matrix harus raise RuntimeError jika graf belum dimuat."""
    handler.graph = None
    with pytest.raises(RuntimeError, match="Graf belum dimuat"):
        handler.compute_distance_matrix(simple_problem)


# ── Tests Euclidean Fallback ──────────────────────────────────────────────────

def test_euclidean_fallback_reasonable_distance(handler):
    """
    Jarak Haversine antara dua titik dekat di Bandar Lampung harus masuk akal
    (antara 1000–2000 meter untuk selisih ~0.01 derajat).
    """
    # Buat mock graph dengan 2 node
    mock_graph = MagicMock()
    mock_graph.nodes = {
        1001: {"y": -5.39, "x": 105.26},   # lat, lon node A
        1002: {"y": -5.40, "x": 105.27},   # lat, lon node B
    }
    handler.graph = mock_graph

    distance = handler._euclidean_fallback(1001, 1002)

    # Verifikasi jarak masuk akal (~1.4 km untuk selisih 0.01°×0.01°)
    assert 1000 <= distance <= 2000, (
        f"Jarak {distance:.1f}m tidak masuk akal untuk dua titik berdekatan"
    )


def test_euclidean_fallback_zero_for_same_point(handler):
    """Jarak fallback dari suatu titik ke dirinya sendiri harus 0."""
    mock_graph = MagicMock()
    mock_graph.nodes = {
        999: {"y": -5.39, "x": 105.26},
    }
    handler.graph = mock_graph

    distance = handler._euclidean_fallback(999, 999)
    assert distance == pytest.approx(0.0, abs=1e-6)


# ── Tests Haversine Helper ────────────────────────────────────────────────────

def test_haversine_known_distance():
    """
    Jarak Haversine antara dua titik dengan selisih ~1° lintang
    harus mendekati ~111 km.
    """
    # 1 derajat lintang ≈ 111,195 meter
    dist = _haversine(0.0, 0.0, 1.0, 0.0)
    assert 110_000 <= dist <= 112_000, f"Haversine: {dist:.0f}m (ekspektasi ~111km)"


def test_haversine_symmetry():
    """Haversine harus simetris: d(A,B) == d(B,A)."""
    d1 = _haversine(-5.39, 105.26, -5.40, 105.27)
    d2 = _haversine(-5.40, 105.27, -5.39, 105.26)
    assert d1 == pytest.approx(d2)
