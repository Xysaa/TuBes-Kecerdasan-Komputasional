# 🧠 Penjelasan Teknis Algoritma

Dokumen ini menjelaskan cara kerja dua algoritma utama:  
**Ant Colony Optimization (ACO)** dan **Fuzzy Logic**, serta bagaimana keduanya diintegrasikan.

---

## 1. Ant Colony Optimization (ACO)

### Inspirasi Biologis
ACO terinspirasi dari perilaku semut nyata mencari jalur terpendek ke sumber makanan.  
Semut meninggalkan jejak **feromon** di jalur yang dilaluinya.  
Semakin pendek jalur, semakin sering dilalui → feromon menumpuk → semut lain ikut.

### Komponen Utama

#### a) Matriks Feromon (τ)
```
τ[i][j] = Intensitas feromon pada edge (i→j)
```
- Diinisialisasi dengan nilai seragam kecil: `τ₀ = 1/n`
- Semakin tinggi nilai τ → edge semakin "menarik"

#### b) Heuristik (η)
```
η[i][j] = 1 / jarak[i][j]
```
- Semakin dekat node j dari node i → η semakin besar
- Dalam proyek ini, η dimodifikasi dengan skor prioritas Fuzzy:
```
η[i][j] = (1 / jarak[i][j]) × (1 + prioritas[j] / 100)
```
→ **Ini adalah titik integrasi Fuzzy Logic ke dalam ACO**

#### c) Probabilitas Pemilihan Node
Setiap semut memilih node berikutnya secara probabilistik:

```
         τ[i][j]^α × η[i][j]^β
P(i→j) = ─────────────────────────────────────────
         Σ (τ[i][k]^α × η[i][k]^β) untuk k ∈ unvisited
```

| Parameter | Simbol | Rekomendasi | Efek |
|-----------|--------|-------------|------|
| Bobot feromon | α | 1.0 | Tinggi → lebih mengikuti jejak lama |
| Bobot heuristik | β | 2-5 | Tinggi → lebih rakus (greedy) |

#### d) Update Feromon
Setelah semua semut selesai, feromon diupdate:

```
1. Evaporasi:  τ[i][j] = (1 - ρ) × τ[i][j]
2. Penguatan:  τ[i][j] += Σ ΔQ/jarak_total  (untuk semut yang lewat i→j)
```

| Parameter | Simbol | Rekomendasi |
|-----------|--------|-------------|
| Laju evaporasi | ρ | 0.1 - 0.5 |
| Konstanta feromon | Q | 100.0 |

### Pseudocode ACO untuk VRP

```
Inisialisasi τ[i][j] = τ₀ untuk semua edge
best_solution = None, best_distance = ∞

UNTUK iterasi = 1 sampai max_iterasi:
    solutions = []

    UNTUK ant = 1 sampai n_ants:
        route = bangun_rute(τ, η, depot, vehicles)
        distance = hitung_total_jarak(route)
        solutions.append((route, distance))

        JIKA distance < best_distance:
            best_distance = distance
            best_solution = route

    update_pheromone(τ, solutions, ρ, Q)

RETURN best_solution, best_distance
```

---

## 2. Fuzzy Logic (Prioritas Paket)

### Mengapa Fuzzy?
Konsep "deadline mendesak" atau "paket berat" tidak bisa dibatasi dengan nilai crisp.
Misal: apakah deadline 6 jam itu "mendesak" atau "normal"?  
Fuzzy Logic memungkinkan nilai keanggotaan **gradual** (0–1), bukan hitam-putih.

### Variabel Input

#### Deadline (jam)
```
mendesak: /‾‾\          [0 - 8 jam]
normal:      /‾‾\       [4 - 20 jam]
santai:          /‾‾    [16 - 24 jam]
         0   8  16   24
```

#### Berat Paket (kg)
```
ringan:  /‾‾\           [0 - 15 kg]
sedang:     /‾‾\        [10 - 40 kg]
berat:          /‾‾     [35 - 50 kg]
         0  15  35   50
```

#### Jarak dari Depot (km)
```
dekat:   /‾‾\           [0 - 20 km]
sedang:     /‾‾\        [15 - 35 km]
jauh:           /‾‾     [30 - 50 km]
         0  20  35   50
```

### Variabel Output: Skor Prioritas (0–100)
```
rendah:  /‾‾\           [0 - 40]
sedang:     /‾‾\        [30 - 70]
tinggi:         /‾‾     [60 - 100]
         0  40  70  100
```

### Rule Base (Contoh)

| # | IF | AND | AND | THEN |
|---|-----|-----|-----|------|
| 1 | deadline = mendesak | — | — | prioritas = tinggi |
| 2 | deadline = santai | berat = ringan | — | prioritas = rendah |
| 3 | berat = berat | jarak = jauh | — | prioritas = tinggi |
| 4 | deadline = normal | berat = sedang | — | prioritas = sedang |
| 5 | jarak = jauh | deadline = mendesak | — | prioritas = tinggi |
| 6 | deadline = normal | berat = ringan | jarak = dekat | prioritas = rendah |

> 📝 Tim bebas menambah rule lain yang masuk akal secara domain.

### Proses Inferensi (Mamdani)

```
Input crisp
    ↓
Fuzzifikasi → hitung derajat keanggotaan setiap input
    ↓
Evaluasi Rule → ambil nilai minimum (AND) atau maksimum (OR)
    ↓
Agregasi → gabungkan semua output rule
    ↓
Defuzzifikasi (Centroid) → konversi ke nilai crisp 0-100
    ↓
Output: skor prioritas
```

---

## 3. Integrasi ACO + Fuzzy

```
┌─────────────────────────────────────────────────────┐
│                    ALUR SISTEM                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Input Lokasi + Atribut Paket                       │
│         │                                           │
│         ▼                                           │
│  FuzzyEvaluator.evaluate_all()                      │
│  → Setiap node.priority diisi (0-100)               │
│         │                                           │
│         ▼                                           │
│  OSMHandler.compute_distance_matrix()               │
│  → dist_matrix terisi jarak jalan nyata             │
│         │                                           │
│         ▼                                           │
│  ACOSolver.solve()                                  │
│  → Dalam _select_next_node():                       │
│      η[i][j] = (1/jarak) × (1 + priority/100)      │
│      ← Fuzzy priority mempengaruhi pilihan rute!   │
│         │                                           │
│         ▼                                           │
│  Output: Rute Optimal + Grafik Konvergensi          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 4. Referensi

- Dorigo, M., & Stützle, T. (2004). *Ant Colony Optimization*. MIT Press.
- Zadeh, L.A. (1965). *Fuzzy sets*. Information and Control, 8(3), 338-353.
- OSMnx Documentation: https://osmnx.readthedocs.io
- scikit-fuzzy Documentation: https://pythonhosted.org/scikit-fuzzy/
