# 🚚 Sistem Optimasi Rute Pengiriman (VRP)
### Berbasis Ant Colony Optimization + Fuzzy Logic + OpenStreetMap

> Tugas Besar Kecerdasan Komputasional — Pengganti UAS  
> Semester Genap 2025/2026

---

## 📌 Deskripsi Singkat

Aplikasi desktop Python yang menyelesaikan **Vehicle Routing Problem (VRP)** —
menentukan rute pengiriman paling efisien untuk beberapa kendaraan ke banyak titik lokasi.

**Metode yang digunakan:**
- 🐜 **Ant Colony Optimization (ACO)** — mencari rute optimal dengan simulasi perilaku semut
- 🔷 **Fuzzy Logic** — mengevaluasi prioritas paket berdasarkan deadline, berat, dan jarak
- 🗺️ **OpenStreetMap (OSM)** — data jalan nyata tanpa biaya via library OSMnx

---

## 👥 Anggota Kelompok

| No | Nama | NIM | Role |
|----|------|-----|------|
| 1  | Rifka Priseilla Br Silitonga | 123140024 |  OSM Handler|
| 2  | Annisa Al-Qoriah | 123140030 | Fuzzy Logic Developer |
| 3  | STEVANUS CAHYA ANGGARA | 123140039 | ACO Engineer |
| 4  | MUHAMMAD RAFLY YAHYA RAMADHAN | 123140148 | GUI Developer|
| 5  | Jefri Wahyu Fernando Sembiring | 123140206 | VRP Model |

---

## 🗂️ Struktur Proyek

```
vrp-aco-fuzzy/
├── main.py                  # Entry point aplikasi
├── requirements.txt         # Daftar dependensi Python
├── README.md
├── core/
│   ├── aco.py               # Algoritma ACO utama
│   ├── vrp_model.py         # Model data VRP (node, depot, kendaraan)
│   └── fuzzy_evaluator.py   # Modul Fuzzy Logic prioritas paket
├── data/
│   ├── osm_handler.py       # Unduh & cache graf jalan dari OSM
│   └── sample_locations.json# Contoh dataset lokasi pengiriman
├── gui/
│   ├── main_window.py       # Window utama PyQt5
│   ├── map_canvas.py        # Kanvas visualisasi peta & rute
│   └── result_panel.py      # Panel hasil, statistik, grafik konvergensi
├── tests/
│   ├── test_aco.py          # Unit test algoritma ACO
│   ├── test_fuzzy.py        # Unit test Fuzzy Logic
│   └── test_osm.py          # Unit test OSM handler
└── docs/
    ├── ALGORITHM.md         # Penjelasan teknis algoritma
    ├── SETUP.md             # Panduan instalasi & menjalankan program
    ├── GITHUB_WORKFLOW.md   # Panduan Git & kolaborasi
    └── CONTRIBUTING.md      # Aturan coding & kontribusi tim
```

---

## ⚡ Quick Start

```bash
# 1. Clone repo
git clone https://github.com/username/vrp-aco-fuzzy.git
cd vrp-aco-fuzzy

# 2. Install dependensi
pip install -r requirements.txt

# 3. Jalankan aplikasi
python main.py
```

Lihat [docs/SETUP.md](docs/SETUP.md) untuk panduan lengkap.

---

## 📚 Dokumentasi

| Dokumen | Isi |
|---------|-----|
| [SETUP.md](docs/SETUP.md) | Cara install, konfigurasi, dan menjalankan |
| [ALGORITHM.md](docs/ALGORITHM.md) | Penjelasan teknis ACO & Fuzzy Logic |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Aturan coding & alur kerja tim |
| [GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md) | Panduan Git & branch strategy |
