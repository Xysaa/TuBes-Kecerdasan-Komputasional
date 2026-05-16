# 🔀 Panduan Git & GitHub Workflow

Panduan ini wajib dibaca semua anggota sebelum mulai ngoding.  
Tujuannya agar kode tidak bentrok dan history commit tetap rapi.

---

## 📌 Struktur Branch

```
main          ← Kode stabil & siap demo. JANGAN push langsung ke sini.
│
├── dev       ← Branch integrasi. Semua fitur di-merge ke sini dulu.
│
├── feat/aco           ← Anggota 1: Algoritma ACO
├── feat/fuzzy         ← Anggota 2: Fuzzy Logic
├── feat/gui           ← Anggota 3: GUI & Layout
├── feat/data-viz      ← Anggota 4: OSM & Visualisasi
└── feat/testing-docs  ← Anggota 5: QA, Testing, Dokumentasi
```

---

## ⚙️ Setup Awal (Lakukan Sekali)

```bash
# 1. Clone repository
git clone https://github.com/<username>/vrp-aco-fuzzy.git
cd vrp-aco-fuzzy

# 2. Buat branch sendiri dari dev
git checkout dev
git checkout -b feat/aco        # sesuaikan dengan branch kamu

# 3. Install dependensi
pip install -r requirements.txt
```

---

## 🔄 Alur Kerja Harian

### Setiap mulai coding:
```bash
# Pastikan branch dev lokal kamu up-to-date
git checkout dev
git pull origin dev

# Pindah ke branch kamu
git checkout feat/aco

# Merge perubahan terbaru dari dev ke branch kamu
git merge dev
```

### Setelah selesai coding:
```bash
# Cek file yang berubah
git status

# Stage file yang ingin di-commit
git add core/aco.py              # spesifik, bukan git add .

# Commit dengan pesan yang jelas
git commit -m "feat: implementasi _init_pheromone dan _build_solutions"

# Push ke GitHub
git push origin feat/aco
```

---

## ✍️ Konvensi Commit Message

Format: `<type>: <deskripsi singkat>`

| Type | Kapan Dipakai | Contoh |
|------|---------------|--------|
| `feat` | Fitur baru | `feat: tambah fuzzy rule untuk jarak jauh` |
| `fix` | Perbaikan bug | `fix: perbaiki index error di _select_next_node` |
| `test` | Tambah/perbaiki test | `test: tambah unit test prioritas tinggi` |
| `docs` | Perubahan dokumentasi | `docs: update README cara install di Windows` |
| `refactor` | Refactor tanpa ubah fungsi | `refactor: ekstrak fungsi heuristik ke method terpisah` |
| `style` | Format kode, bukan logic | `style: rapikan indentasi di vrp_model.py` |

**Tips:**
- Gunakan kata kerja imperatif: "tambah", "perbaiki", "hapus" — bukan "menambahkan"
- Maksimal 72 karakter untuk judul commit
- Jika perlu penjelasan panjang, tambahkan baris kosong lalu tulis detail di bawah

---

## 🔁 Cara Buat Pull Request (PR) ke `dev`

1. Push branch kamu ke GitHub
2. Buka GitHub → klik **"Compare & pull request"**
3. Set: `base: dev` ← `compare: feat/aco`
4. Isi deskripsi PR:
   ```
   ## Yang sudah dikerjakan
   - Implementasi _init_pheromone
   - Implementasi _build_solutions (draft)

   ## Yang belum selesai
   - _update_pheromone (akan di-PR berikutnya)

   ## Cara test
   pytest tests/test_aco.py
   ```
5. Minta **minimal 1 anggota lain** untuk review
6. Setelah di-approve, merge menggunakan **"Squash and merge"**

---

## ⚠️ Aturan Wajib

- ❌ **DILARANG** push langsung ke `main` atau `dev`
- ❌ **DILARANG** `git push --force` ke branch bersama
- ✅ Selalu jalankan `pytest` sebelum buat PR
- ✅ Resolve conflict di branch sendiri, bukan di `dev`
- ✅ Komunikasikan di grup jika mau mengubah file yang bukan tanggung jawabmu

---

## 🛠️ Resolusi Conflict

Jika ada conflict saat merge:
```bash
# Lihat file yang conflict
git status

# Buka file conflict, cari tanda ini:
# <<<<<<< HEAD
# kode kamu
# =======
# kode dari dev
# >>>>>>> dev

# Edit manual → hapus tanda conflict → simpan file

# Stage file yang sudah diperbaiki
git add <nama_file>
git commit -m "fix: resolve conflict di aco.py"
```

---

## 📅 Jadwal Sync Rutin

| Waktu | Kegiatan |
|-------|----------|
| Setiap pagi (sebelum coding) | `git pull origin dev` |
| Setiap selesai fitur | Buat PR ke `dev` |
| Akhir Minggu 1 | Merge semua ke `dev`, demo internal |
| Hari 9 | Merge `dev` ke `main` untuk versi final |
