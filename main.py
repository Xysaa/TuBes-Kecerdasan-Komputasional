"""
main.py — Entry Point Aplikasi VRP-ACO-Fuzzy
=============================================
File ini adalah titik masuk utama aplikasi.
Tugasnya:
  1. Inisialisasi aplikasi PyQt5
  2. Membuat dan menampilkan window utama
  3. Menangani exception global jika perlu

PIC: Anggota 3 (GUI Developer) — koordinasi dengan semua anggota
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """
    Fungsi utama untuk menjalankan aplikasi.

    TODO:
    - Inisialisasi QApplication dengan sys.argv
    - Buat instance MainWindow
    - Tampilkan window (window.show())
    - Jalankan event loop (app.exec_())
    - Return exit code ke sys.exit()
    """
    pass


if __name__ == "__main__":
    main()
