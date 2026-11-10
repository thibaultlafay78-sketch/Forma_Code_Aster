# -*- coding: utf-8 -*-
"""Étape 2 — figure E2_rayleigh.png : barres groupées (CALC_MODES, Rayleigh,
note) pour les deux configurations (ressorts / base encastrée).

Usage : python Etape2/E2_post.py   (après exécution de E2_modal_rayleigh.export)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402
from post_utils import plt  # noqa: E402

r = pu.lire_csv(pu.chemin("Etape2", "resultats", "E2_rayleigh.csv"))
configs = list(r["config"])
labels = {"RESSORTS": "Base sur ressorts", "ENCASTRE": "Base encastrée"}

series = [("CALC_MODES", r["f_calc_modes_Hz"]),
          ("Rayleigh (déformée statique m·g)", r["f_rayleigh_Hz"]),
          ("Note Maurel", r["f_note_Hz"])]

x = np.arange(len(configs))
larg = 0.26
fig, ax = plt.subplots(figsize=(7, 4.5))
for k, (nom, vals) in enumerate(series):
    b = ax.bar(x + (k - 1) * larg, vals, larg, label=nom)
    ax.bar_label(b, fmt="%.2f", fontsize=8)
ax.set_xticks(x)
ax.set_xticklabels([labels.get(c, c) for c in configs])
ax.set_ylabel("Fréquence fondamentale (Hz)")
ax.set_title("Fréquence fondamentale : calcul modal, Rayleigh et note")
ax.legend(loc="upper left", fontsize=8)
ax.grid(axis="y", alpha=0.3)

pu.sauver_figure(fig, "Etape2", "E2_rayleigh", {
    "config": configs,
    "f_calc_modes_Hz": r["f_calc_modes_Hz"],
    "f_rayleigh_Hz": r["f_rayleigh_Hz"],
    "f_note_Hz": r["f_note_Hz"],
})

for c, fm, fr in zip(configs, r["f_calc_modes_Hz"], r["f_rayleigh_Hz"]):
    flag = "OK (Rayleigh >= exacte)" if fr >= fm else "ATTENTION : Rayleigh < exacte"
    print("%-9s  modes %.3f Hz  Rayleigh %.3f Hz  écart %+.1f %%  %s"
          % (c, fm, fr, 100 * (fr / fm - 1), flag))
