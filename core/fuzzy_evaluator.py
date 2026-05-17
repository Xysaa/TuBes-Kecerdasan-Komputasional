"""
core/fuzzy_evaluator.py — Modul Fuzzy Logic Prioritas Paket
=============================================================
Menentukan skor prioritas (0–100) untuk setiap paket pengiriman
berdasarkan tiga variabel input menggunakan Fuzzy Inference System (FIS).

Variabel Input:
  1. deadline_jam  : Sisa waktu deadline (0–24 jam)
  2. berat_kg      : Berat paket (0–50 kg)
  3. jarak_km      : Jarak node dari depot (0–50 km)
     → Semakin jauh, semakin tinggi prioritas karena lebih sulit dijangkau

Variabel Output:
  - prioritas (0–100)
    0–33   : Rendah
    34–66  : Sedang
    67–100 : Tinggi

Membership Functions: Triangular (trimf) menggunakan scikit-fuzzy

Referensi: https://pythonhosted.org/scikit-fuzzy/

PIC: Annisa (Fuzzy Logic Developer)
Kolaborasi: Stevanus (integrasi skor ke ACO heuristik)
"""

import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl
from core.vrp_model import DeliveryNode


class FuzzyEvaluator:
    """
    Evaluator berbasis Fuzzy Logic untuk menentukan prioritas pengiriman.
    """

    def __init__(self):
        self.simulation = self._build_fuzzy_system()

    def _build_fuzzy_system(self):
        """
        Bangun Fuzzy Inference System menggunakan scikit-fuzzy.
        """
        # ── Step 1: Definisi Antecedent & Consequent ──────────────────────────
        deadline  = ctrl.Antecedent(np.arange(0, 25, 1),  'deadline_jam')
        berat     = ctrl.Antecedent(np.arange(0, 51, 1),  'berat_kg')
        jarak     = ctrl.Antecedent(np.arange(0, 51, 1),  'jarak_km')
        prioritas = ctrl.Consequent(np.arange(0, 101, 1), 'prioritas')

        # ── Step 2: Membership Functions (trimf) ──────────────────────────────
        deadline['mendesak'] = fuzz.trimf(deadline.universe,  [0,  0,  8])
        deadline['normal']   = fuzz.trimf(deadline.universe,  [4,  12, 20])
        deadline['santai']   = fuzz.trimf(deadline.universe,  [16, 24, 24])

        berat['ringan'] = fuzz.trimf(berat.universe, [0,  0,  15])
        berat['sedang'] = fuzz.trimf(berat.universe, [10, 25, 40])
        berat['berat']  = fuzz.trimf(berat.universe, [35, 50, 50])

        jarak['dekat']  = fuzz.trimf(jarak.universe, [0,  0,  20])
        jarak['sedang'] = fuzz.trimf(jarak.universe, [15, 25, 35])
        jarak['jauh']   = fuzz.trimf(jarak.universe, [30, 50, 50])

        prioritas['rendah']  = fuzz.trimf(prioritas.universe, [0,  0,  40])
        prioritas['sedang']  = fuzz.trimf(prioritas.universe, [30, 50, 70])
        prioritas['tinggi']  = fuzz.trimf(prioritas.universe, [60, 100, 100])

        # ── Step 3: Rule Base ─────────────────────────────────────────────────
        rule1 = ctrl.Rule(deadline['mendesak'],
                          prioritas['tinggi'])

        rule2 = ctrl.Rule(deadline['santai'] & berat['ringan'],
                          prioritas['rendah'])

        rule3 = ctrl.Rule(berat['berat'] & jarak['jauh'],
                          prioritas['tinggi'])

        rule4 = ctrl.Rule(deadline['normal'] & berat['sedang'],
                          prioritas['sedang'])

        rule5 = ctrl.Rule(jarak['jauh'] & deadline['mendesak'],
                          prioritas['tinggi'])

        rule6 = ctrl.Rule(deadline['normal'] & berat['ringan'] & jarak['dekat'],
                          prioritas['rendah'])

        rule7 = ctrl.Rule(deadline['santai'] & jarak['jauh'],
                          prioritas['sedang'])

        rule8 = ctrl.Rule(berat['berat'] & deadline['normal'],
                          prioritas['sedang'])

        rule9 = ctrl.Rule(deadline['santai'] & berat['berat'] & jarak['jauh'],
                          prioritas['sedang'])

        rule10 = ctrl.Rule(deadline['mendesak'] & berat['ringan'],
                           prioritas['tinggi'])

        # ── Step 4: Buat Control System & Simulation ──────────────────────────
        sistem_ctrl = ctrl.ControlSystem([
            rule1, rule2, rule3, rule4, rule5,
            rule6, rule7, rule8, rule9, rule10
        ])
        return ctrl.ControlSystemSimulation(sistem_ctrl)

    def evaluate(self, node: DeliveryNode, distance_from_depot_km: float) -> float:
        """
        Hitung skor prioritas untuk satu node pengiriman.

        Parameter:
          node                    : DeliveryNode yang akan dievaluasi
          distance_from_depot_km  : Jarak node dari depot dalam kilometer

        Return:
          float: Skor prioritas (0.0 – 100.0)
        """
        try:
            # Clamp nilai input agar tidak keluar dari universe of discourse
            deadline_val = float(np.clip(node.deadline_h, 0, 24))
            berat_val    = float(np.clip(node.weight_kg, 0, 50))
            jarak_val    = float(np.clip(distance_from_depot_km, 0, 50))

            self.simulation.input['deadline_jam'] = deadline_val
            self.simulation.input['berat_kg']     = berat_val
            self.simulation.input['jarak_km']     = jarak_val

            self.simulation.compute()
            return float(self.simulation.output['prioritas'])

        except Exception:
            # Fallback ke prioritas sedang jika terjadi error
            return 50.0

    def evaluate_all(self, nodes: list, dist_matrix: list, depot_index: int = 0) -> list:
        """
        Evaluasi prioritas untuk semua node sekaligus.

        Parameter:
          nodes       : list[DeliveryNode]
          dist_matrix : matriks jarak (meter), index 0 = depot
          depot_index : index depot di dist_matrix (default 0)

        Return:
          list[float]: skor prioritas untuk setiap node (urutan sama dengan input)
        """
        scores = []
        for i, node in enumerate(nodes):
            # Index di dist_matrix: depot = 0, node ke-i = i+1
            distance_m  = dist_matrix[depot_index][i + 1]
            distance_km = distance_m / 1000.0

            score = self.evaluate(node, distance_km)
            node.priority = score
            scores.append(score)

        return scores

    def get_priority_label(self, score: float) -> str:
        """
        Konversi skor numerik ke label teks.

        Return:
          "🟢 Rendah"  jika score < 34
          "🟡 Sedang"  jika 34 <= score < 67
          "🔴 Tinggi"  jika score >= 67
        """
        if score < 34:
            return "🟢 Rendah"
        elif score < 67:
            return "🟡 Sedang"
        else:
            return "🔴 Tinggi"