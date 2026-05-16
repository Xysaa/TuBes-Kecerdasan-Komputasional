# 🤝 Panduan Kontribusi Tim

Dokumen ini berisi aturan coding dan kolaborasi yang disepakati bersama.  
Tujuannya agar kode seluruh anggota konsisten dan mudah dibaca satu sama lain.

---

## 🐍 Konvensi Kode Python (PEP 8)

### Penamaan
```python
# Variabel & fungsi → snake_case
total_distance = 0.0
def compute_distance_matrix():
    pass

# Kelas → PascalCase
class ACOSolver:
    pass

# Konstanta → UPPER_SNAKE_CASE
MAX_ITERATIONS = 500
VEHICLE_COLORS = ["#E74C3C", "#2ECC71"]

# "Private" (hanya dipakai dalam kelas) → awalan underscore
def _init_pheromone(self):
    pass
```

### Formatting
```python
# Indentasi: 4 spasi (BUKAN tab)
def my_function():
    if condition:
        do_something()

# Spasi di sekitar operator
x = a + b           # ✅
x=a+b               # ❌

# Spasi setelah koma
f(a, b, c)          # ✅
f(a,b,c)            # ❌

# Baris maksimal 100 karakter
# Jika lebih panjang, pecah dengan backslash atau kurung
result = (some_long_variable_name
          + another_long_variable_name)
```

### Docstring
Setiap fungsi publik WAJIB punya docstring minimal satu baris:
```python
def evaluate(self, node, distance_km):
    """Hitung skor prioritas untuk satu node pengiriman."""
    pass

# Untuk fungsi kompleks, gunakan format lengkap:
def solve(self, callback=None):
    """
    Jalankan algoritma ACO dan return solusi terbaik.

    Parameter:
        callback (callable): Dipanggil setiap iterasi, signature: f(iter, dist)

    Return:
        dict: {'routes': ..., 'distance': ..., 'history': ...}
    """
    pass
```

---

## 📁 Aturan File & Modul

- Satu file = satu tanggung jawab jelas
- Import diurutkan: stdlib → third-party → local
  ```python
  import os                    # stdlib
  import numpy as np           # third-party
  from core.vrp_model import * # local
  ```
- Hindari `import *` — selalu import spesifik
- Tidak ada kode yang berjalan saat file di-import (gunakan `if __name__ == "__main__":`)

---

## ✅ Standar Testing

- Setiap fungsi publik harus punya minimal 1 test
- Nama test harus deskriptif: `test_<apa_yang_ditest>_<kondisi>`
  ```python
  def test_evaluate_urgent_deadline_gives_high_priority():  # ✅
  def test_func1():                                          # ❌
  ```
- Gunakan fixture pytest untuk data yang dipakai ulang
- Mock koneksi internet / filesystem di semua test (jangan test yang butuh internet)
- Jalankan `pytest` sebelum setiap PR — pastikan semua test lulus

---

## 🔍 Code Review Checklist

Sebelum approve PR anggota lain, pastikan:

- [ ] Semua fungsi baru punya docstring
- [ ] Tidak ada `print()` debug yang tertinggal (gunakan `logging` jika perlu)
- [ ] Tidak ada hardcoded path absolut (misal: `C:\Users\nama\...`)
- [ ] Semua test masih lulus setelah perubahan
- [ ] Tidak ada file cache atau `__pycache__` yang ikut di-commit
- [ ] Kode mudah dibaca tanpa harus tanya penulisnya

---

## 💬 Komunikasi Tim

- Gunakan grup WhatsApp/Discord untuk koordinasi harian
- Jika ada perubahan yang menyentuh file milik anggota lain → diskusikan dulu
- Laporkan blocker (hambatan) ke grup segera, jangan tunggu sampai deadline
- Review PR dalam 24 jam setelah dibuat

---

## 📝 .gitignore (sudah ada di repo)

File-file berikut tidak perlu di-commit:
```
__pycache__/
*.pyc
venv/
.env
data/cache/          ← file graphml OSM bisa sangat besar
*.graphml
results/
*.csv
*.log
```
