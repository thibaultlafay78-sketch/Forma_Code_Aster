# -*- coding: utf-8 -*-
"""Étape 2 — figure E2_rayleigh.png (+ .svg, .csv) : barres groupées
(CALC_MODES, Rayleigh) pour les deux configurations ; la valeur de la note de
référence (4,79 Hz) n'est tracée que pour la base sur ressorts, seule
configuration à laquelle elle correspond.

Usage : python Etape2/E2_post.py   (après exécution de E2_modal_rayleigh.export)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402

r = pu.lire_csv(pu.chemin("Etape2", "resultats", "E2_rayleigh.csv"))
configs = list(r["config"])
labels = {"RESSORTS": "Base sur ressorts", "ENCASTRE": "Base encastrée"}
# 4,79 Hz : base sur ressorts uniquement (retouche v2.1) ; NaN = pas de barre
f_ref = np.array([fn if c == "RESSORTS" else np.nan for c, fn in zip(configs, r["f_note_Hz"])])

series = [("CALC_MODES", r["f_calc_modes_Hz"]),
          ("Rayleigh (déformée statique m·g)", r["f_rayleigh_Hz"]),
          ("Note de référence", f_ref)]

x = np.arange(len(configs))
larg = 0.26
fig, ax = pu.nouvelle_figure(figsize=(7, 4.5))
for k, (nom, vals) in enumerate(series):
    ok = ~np.isnan(vals)
    b = ax.bar(x[ok] + (k - 1) * larg, vals[ok], larg, label=nom, color=pu.couleur(k))
    ax.bar_label(b, fmt="%.2f", fontsize=pu.STYLE["taille_etiquette"])
ax.set_xticks(x)
ax.set_xticklabels([labels.get(c, c) for c in configs])
ax.set_ylabel("Fréquence fondamentale (Hz)")
ax.legend(loc="upper left")
ax.grid(False, axis="x")

pu.sauver_figure(fig, "Etape2", "E2_rayleigh", {
    "config": configs,
    "f_calc_modes_Hz": r["f_calc_modes_Hz"],
    "f_rayleigh_Hz": r["f_rayleigh_Hz"],
    "f_note_reference_Hz": f_ref,
})

for c, fm, fr in zip(configs, r["f_calc_modes_Hz"], r["f_rayleigh_Hz"]):
    flag = "OK (Rayleigh >= exacte)" if fr >= fm else "ATTENTION : Rayleigh < exacte"
    print("%-9s  modes %.3f Hz  Rayleigh %.3f Hz  écart %+.1f %%  %s"
          % (c, fm, fr, 100 * (fr / fm - 1), flag))
