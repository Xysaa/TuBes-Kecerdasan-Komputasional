"""
main.py — Entry Point Aplikasi VRP-ACO-Fuzzy
=============================================
File ini adalah titik masuk utama aplikasi.
Tugasnya:
  1. Inisialisasi aplikasi PyQt5
  2. Membuat dan menampilkan window utama
  3. Menangani exception global jika perlu

PIC: Rafly (GUI Developer) — koordinasi dengan semua anggota
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Inisialisasi dan jalankan aplikasi VARCO."""
    app    = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()