# -*- coding: utf-8 -*-
"""Étape 5 — figure E5_surface_2entrees.png : spectres à 5 % en surface pour
les deux lectures du signal (RA, CL) et leur rapport (second axe).

Lit les fichiers IMPR_FONCTION (FORMAT='TABLEAU') produits par DEFI_SOL_EQUI.
La colonne d'accélération en surface est repérée par SURFACE_COL (légende
« AX_CL » dans la macro v18.1.11 : en entrée RA c'est le champ libre calculé,
en entrée CL c'est le signal imposé). À vérifier sur un premier fichier produit.
Le nombre d'itérations est relu dans resultats/E5.mess.

Usage : python Etape5/E5_post.py
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402
from post_utils import plt  # noqa: E402

SURFACE_COL = "AX_CL"


def lire_tableau(path):
    """Retourne {légende: (x, y)} pour chaque courbe d'un fichier IMPR_FONCTION
    FORMAT='TABLEAU'. Structure d'un bloc (v18.1.11) :
        ## Courbe k
        ## <LÉGENDE> ...        (ex. AX_CL, AX_RA, AX_1 …, AX_BH)
        INST  ACCE_0  ACCE_1 …  (en-tête : colonne k+1 = courbe k)
        valeurs…
    """
    courbes, legendes, lignes = {}, [], []
    attendre_legende = False

    def vider():
        if lignes and legendes:
            arr = np.array(lignes)
            for k, nom in enumerate(legendes):
                if k + 1 < arr.shape[1]:
                    courbes.setdefault(nom, (arr[:, 0], arr[:, k + 1]))

    with open(path, encoding="utf-8", errors="replace") as f:
        for l in f:
            s = l.strip()
            if s.startswith("## Courbe"):
                attendre_legende = True
                continue
            if s.startswith("##") and attendre_legende:
                legendes.append(s.lstrip("#").split()[0])
                attendre_legende = False
                continue
            if s.startswith("#"):
                if s.startswith("#-") or s.startswith("###"):   # nouveau bloc
                    vider()
                    legendes, lignes = [], []
                continue
            try:
                vals = [float(x.replace("D", "E")) for x in s.split()]
                if vals:
                    lignes.append(vals)
            except ValueError:
                pass   # ligne d'en-tête (INST ACCE_0 …)
    vider()
    return courbes


def surface(calcul):
    c = lire_tableau(pu.chemin("Etape5", "resultats", "E5_%s_tran.txt" % calcul))
    cle = next((k for k in c if k.startswith(SURFACE_COL)), None)
    if cle is None:
        raise KeyError("%s absent de E5_%s_tran.txt ; colonnes : %s" % (SURFACE_COL, calcul, list(c)))
    return c[cle]


spec = {}
for calc in ("RA", "CL"):
    t, a = surface(calc)
    spec[calc] = pu.spectre_oscillateur(t, a / pu.G, pu.FREQS, 0.05)
rapport = spec["RA"] / spec["CL"]

iters = re.findall(r"CONVERGENCE ATTEINTE NOMBRE ITERATIONS=\s*(\d+)",
                   open(pu.chemin("Etape5", "resultats", "E5.mess"), errors="replace").read())
print("itérations (RA, CL) :", iters)

ref_path = pu.chemin("Etape5", "resultats", "E5_reference_python.csv")
ref = pu.lire_csv(ref_path) if os.path.exists(ref_path) else None

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(pu.FREQS, spec["RA"], lw=1.8, label="Signal au rocher affleurant (RA)")
ax.plot(pu.FREQS, spec["CL"], lw=1.8, label="Signal en surface, champ libre (CL)")
if ref is not None:
    ax.plot(ref["freq_Hz"], ref["surface_RA_g"], ":", color="C0", lw=1, label="RA, référence Python")
    ax.plot(ref["freq_Hz"], ref["surface_BH_g"], ":", color="grey", lw=1,
            label="En profondeur, base rigide (Python)")
pu.axes_spectre(ax, "Spectres en surface à 5 %% — deux lectures du signal %s" %
                ("(itérations RA/CL : %s)" % "/".join(iters) if iters else ""))
ax2 = ax.twinx()
ax2.plot(pu.FREQS, rapport, "k--", lw=1, label="Rapport RA / CL")
ax2.axhline(1.0, color="k", lw=0.5)
ax2.set_ylabel("Rapport RA / CL (–)")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper left")

pu.sauver_figure(fig, "Etape5", "E5_surface_2entrees", {
    "freq_Hz": pu.FREQS, "surface_RA_g": spec["RA"], "surface_CL_g": spec["CL"],
    "rapport_RA_CL": rapport})
