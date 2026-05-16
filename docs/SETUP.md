# ⚙️ Panduan Instalasi & Setup

---

## Prasyarat

| Software | Versi Minimum | Cek dengan |
|----------|---------------|------------|
| Python | 3.10+ | `python --version` |
| pip | 22+ | `pip --version` |
| Git | 2.30+ | `git --version` |

---

## Langkah Instalasi

### 1. Clone Repository
```bash
git clone https://github.com/<username>/vrp-aco-fuzzy.git
cd vrp-aco-fuzzy
```

### 2. Buat Virtual Environment (Rekomendasi)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

> ⏳ Proses install mungkin memakan waktu 3-5 menit karena OSMnx cukup besar.

### 4. Jalankan Aplikasi
```bash
python main.py
```

---

## Troubleshooting

### ❌ Error saat install `osmnx` di Windows
OSMnx membutuhkan library geospasial yang kadang bermasalah di Windows.

**Solusi:**
```bash
# Install dulu dari conda (lebih stabil untuk Windows)
conda install -c conda-forge osmnx

# Atau install Microsoft C++ Build Tools dari:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### ❌ Error: `No module named 'PyQt5'`
```bash
pip install PyQt5 --force-reinstall
```

### ❌ Aplikasi crash saat unduh graf OSM
Kemungkinan tidak ada koneksi internet atau area tidak ditemukan.
- Pastikan koneksi internet aktif saat pertama kali load graf
- Coba ganti nama kota di pengaturan: `"Kota Bandar Lampung, Lampung, Indonesia"`
- Setelah graf berhasil diunduh, simpan cache agar tidak perlu unduh ulang

### ❌ Graf unduhan terlalu besar / lambat
```python
# Di data/osm_handler.py, ganti ke area lebih kecil:
# Dari:
ox.graph_from_place("Bandar Lampung, Indonesia", network_type='drive')
# Ke (contoh: hanya satu kecamatan):
ox.graph_from_place("Kedaton, Bandar Lampung, Indonesia", network_type='drive')
```

---

## Menjalankan Tests
```bash
# Semua test
pytest

# Test spesifik satu modul
pytest tests/test_aco.py -v

# Test dengan laporan coverage
pip install pytest-cov
pytest --cov=core tests/
```

---

## Struktur Data Cache

Setelah pertama kali dijalankan, folder berikut akan terbuat otomatis:
```
data/cache/
└── osm_graph.graphml    ← Cache graf jalan (bisa berukuran 50-200 MB)
```

File ini **tidak perlu** di-commit ke GitHub (sudah ada di `.gitignore`).
