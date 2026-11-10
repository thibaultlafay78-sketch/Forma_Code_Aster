# -*- coding: utf-8 -*-
"""Étape 5 — calcul de référence indépendant (linéaire équivalent, ondes SH
verticales, méthode des matrices de transfert type SHAKE ; Kramer 1996 §7.2).

Trois lectures d'un même signal :
  RA : signal = rocher affleurant (outcrop) au toit du substratum   R = 2·A_N+1
  CL : signal = surface du champ libre (déconvolution)              R = 2
  BH : signal = en profondeur, toit du substratum, base rigide       R = A_N+1 + B_N+1
       (« within » ; non disponible dans DEFI_SOL_EQUI v18.1.11)

Hypothèses : module complexe G* = G(1 + 2iξ) ; γeff = 0,65·γmax à mi-hauteur
de chaque sous-couche ; courbes de la couche (sous-couche centrale) appliquées
à toutes ses sous-couches ; substratum linéaire ξ = 1 %. Pour la déconvolution
(CL), les fréquences au-delà de F_COUPURE sont annulées (instabilité).

Sorties : resultats/E5_reference_python.csv (spectres de surface à 5 %, g)
          resultats/E5_reference_proprietes.csv (G et ξ convergés, itérations)
Usage : python Etape5/E5_reference_python.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402

SIGNAL = 1
COEF_GAMMA = 0.65
NMAX_ITER = 20
TOL = 0.01
F_COUPURE = 30.0      # Hz

col = pu.lire_csv(pu.chemin("Etape5", "donnees", "E5_colonne.csv"))
cv = pu.lire_csv(pu.chemin("Etape5", "donnees", "E5_darendeli.csv"))
sig = pu.lire_csv(pu.chemin("Etape3", "resultats", "E3_signaux.csv"))

noms = list(col["sous_couche"])
iN = noms.index("SUBST")
h = np.array([col["z_bas_m"][i] - col["z_haut_m"][i] for i in range(iN)], dtype=float)
rho = np.array(col["rho_kg_m3"], dtype=float)
vs = np.array(col["vs_m_s"], dtype=float)
gmax = rho * vs ** 2
mate = np.array(col["nume_mate"], dtype=int)
dmin = np.array(col["Dmin_pct"][:iN], dtype=float) / 100.0
NOMS_MAT = {1: "limon", 2: "sable", 3: "sable_tres_dense", 4: "marne"}
lg = np.log10(cv["gamma_pct"])


def courbes(m, gamma_pct):
    x = np.log10(np.clip(gamma_pct, cv["gamma_pct"][0], cv["gamma_pct"][-1]))
    return (np.interp(x, lg, cv["GG_" + NOMS_MAT[m]]),
            np.interp(x, lg, cv["D_%s_pct" % NOMS_MAT[m]]) / 100.0)


t = sig["t_s"]
acc = sig["acc%d_m_s2" % SIGNAL]
dt = t[1] - t[0]
n = int(2 ** np.ceil(np.log2(len(acc) * 2)))
A_in = np.fft.rfft(acc, n)
w = 2 * np.pi * np.fft.rfftfreq(n, dt)
w[0] = 1e-6


def amplitudes(G, xi):
    """A_m, B_m (m = 0..N, N = substratum) pour A_0 = B_0 = 1 en surface."""
    Gs = G * (1 + 2j * xi)
    vss = np.sqrt(Gs / rho)
    k = w[None, :] / vss[:, None]
    A = np.ones((iN + 1, len(w)), complex)
    B = np.ones((iN + 1, len(w)), complex)
    for m in range(iN):
        a = rho[m] * vss[m] / (rho[m + 1] * vss[m + 1])
        e, ei = np.exp(1j * k[m] * h[m]), np.exp(-1j * k[m] * h[m])
        A[m + 1] = 0.5 * A[m] * (1 + a) * e + 0.5 * B[m] * (1 - a) * ei
        B[m + 1] = 0.5 * A[m] * (1 - a) * e + 0.5 * B[m] * (1 + a) * ei
    return A, B, k


def calcul(lecture):
    G = gmax.copy()
    xi = np.append(dmin, 0.01)
    for it in range(1, NMAX_ITER + 1):
        A, B, k = amplitudes(G, xi)
        R = {"RA": 2 * A[iN], "CL": 2 * np.ones(len(w)), "BH": A[iN] + B[iN]}[lecture]
        scale = A_in / R
        if lecture == "CL":
            scale[w / (2 * np.pi) > F_COUPURE] = 0.0
        disp = -scale / w ** 2
        G_new, xi_new = G.copy(), xi.copy()
        for m in range(iN):
            z = h[m] / 2
            gam_w = 1j * k[m] * (A[m] * np.exp(1j * k[m] * z) - B[m] * np.exp(-1j * k[m] * z)) * disp
            gmax_t = np.abs(np.fft.irfft(gam_w, n)).max()
            gg, d = courbes(mate[m], 100.0 * COEF_GAMMA * gmax_t)
            G_new[m], xi_new[m] = gg * gmax[m], d
        ecart = np.max(np.abs(G_new[:iN] / G[:iN] - 1))
        G, xi = G_new, xi_new
        if ecart < TOL:
            break
    A, B, _ = amplitudes(G, xi)
    R = {"RA": 2 * A[iN], "CL": 2 * np.ones(len(w)), "BH": A[iN] + B[iN]}[lecture]
    scale = A_in / R
    if lecture == "CL":
        # en lecture CL, la surface est le signal imposé lui-même (la coupure
        # ne sert qu'au calcul des déformations dans la colonne)
        return acc.copy(), G, xi, it
    surf = np.fft.irfft(2 * scale, n)[:len(acc)]
    return surf, G, xi, it


res = {}
props = {"calcul": [], "sous_couche": [], "G_MPa": [], "G_Gmax": [], "xi_pct": [], "iterations": []}
for lec in ("RA", "CL", "BH"):
    surf, G, xi, it = calcul(lec)
    res[lec] = pu.spectre_oscillateur(t, surf / pu.G, pu.FREQS, 0.05)
    for m in range(iN):
        props["calcul"].append(lec); props["sous_couche"].append(noms[m])
        props["G_MPa"].append(G[m] / 1e6); props["G_Gmax"].append(G[m] / gmax[m])
        props["xi_pct"].append(100 * xi[m]); props["iterations"].append(it)
    print("%s : %d itérations, PGA surface = %.3f g" % (lec, it, np.abs(surf).max() / pu.G))

pu.ecrire_csv(pu.chemin("Etape5", "resultats", "E5_reference_python.csv"),
              {"freq_Hz": pu.FREQS, "surface_RA_g": res["RA"], "surface_CL_g": res["CL"],
               "surface_BH_g": res["BH"]})
pu.ecrire_csv(pu.chemin("Etape5", "resultats", "E5_reference_proprietes.csv"), props)
