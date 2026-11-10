# -*- coding: utf-8 -*-
"""Étape 3 — figures et tableau de contrôle (guide ASN 2/01 §2.2.3).

Sorties :
  figures/E3_signaux.png (+ .csv)    les 3 signaux, en g
  figures/E3_spectres.png (+ .csv)   spectres à 5 %, moyen et cible
  resultats/E3_controle.csv          tableau de contrôle des critères
  resultats/E3_intercorrelation.csv  coefficients deux à deux

Usage : python Etape3/E3_post.py   (après E3_accelerogrammes.export)
"""
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402
from post_utils import plt  # noqa: E402

# Définition de l'intercorrélation : >>> À RELIRE AVEC BASILE.
#   "GLOBAL"  : coefficient de Pearson sur toute la durée ;
#   "FENETRE" : max |ρ| sur fenêtres glissantes de FENETRE_S secondes.
INTERCORR = "GLOBAL"
FENETRE_S = 5.0
CONTROLE_PYTHON = True   # recalcul indépendant des spectres à 5 % (Newmark)

sig = pu.lire_csv(pu.chemin("Etape3", "resultats", "E3_signaux.csv"))
spe = pu.lire_csv(pu.chemin("Etape3", "resultats", "E3_spectres.csv"))
t = sig["t_s"]
noms = [k for k in sig if k.startswith("acc")]
accs = [sig[k] for k in noms]
f = spe["freq_Hz"]
dt = t[1] - t[0]

# --- Figure E3_signaux ---------------------------------------------------------
fig, axs = plt.subplots(len(accs), 1, figsize=(8, 6), sharex=True)
for i, (ax, a) in enumerate(zip(axs, accs)):
    ax.plot(t, a / pu.G, lw=0.6)
    ax.set_ylabel("Acc. (g)")
    ax.set_title("Signal %d — PGA = %.3f g" % (i + 1, np.abs(a).max() / pu.G), fontsize=9)
    ax.grid(alpha=0.3)
axs[-1].set_xlabel("Temps (s)")
pu.sauver_figure(fig, "Etape3", "E3_signaux",
                 {"t_s": t, **{"acc%d_g" % (i + 1): a / pu.G for i, a in enumerate(accs)}})

# --- Figure E3_spectres (5 %) -------------------------------------------------
s5 = [spe["s%d_05" % (i + 1)] for i in range(len(accs))]
moy5 = np.mean(s5, axis=0)
fig, ax = plt.subplots(figsize=(8, 5))
for i, s in enumerate(s5):
    ax.plot(f, s, lw=0.7, alpha=0.6, label="Signal %d" % (i + 1))
ax.plot(f, moy5, "k", lw=1.8, label="Moyenne des 3 signaux")
ax.plot(f, spe["cible_05"], "r--", lw=1.8, label="Spectre cible (EC8 zone 3, sol B)")
colonnes = {"freq_Hz": f, **{"s%d_g" % (i + 1): s for i, s in enumerate(s5)},
            "moyenne_g": moy5, "cible_g": spe["cible_05"]}
if CONTROLE_PYTHON:
    s5py = np.mean([pu.spectre_oscillateur(t, a / pu.G, f, 0.05) for a in accs], axis=0)
    ax.plot(f, s5py, ":", color="grey", lw=1.2, label="Moyenne, recalcul Python")
    colonnes["moyenne_python_g"] = s5py
pu.axes_spectre(ax, "Spectres de réponse à 5 % d'amortissement")
ax.legend(fontsize=8)
pu.sauver_figure(fig, "Etape3", "E3_spectres", colonnes)


# --- Intercorrélation ---------------------------------------------------------
def rho(a, b):
    if INTERCORR == "GLOBAL":
        return np.corrcoef(a, b)[0, 1]
    n = int(FENETRE_S / dt)
    vals = [np.corrcoef(a[k:k + n], b[k:k + n])[0, 1] for k in range(0, len(a) - n, n // 2)]
    return max(vals, key=abs)


paires = list(itertools.combinations(range(len(accs)), 2))
rhos = [rho(accs[i], accs[j]) for i, j in paires]
pu.ecrire_csv(pu.chemin("Etape3", "resultats", "E3_intercorrelation.csv"), {
    "signal_i": [i + 1 for i, _ in paires], "signal_j": [j + 1 for _, j in paires],
    "rho": rhos, "definition": [INTERCORR] * len(paires)})

# --- Tableau de contrôle -----------------------------------------------------
crit, exig, resu, ok = [], [], [], []


def ligne(c, e, r, b):
    crit.append(c); exig.append(e); resu.append(r); ok.append("OUI" if b else "NON")


ligne("Nombre de signaux", ">= 3 par jeu", "%d" % len(accs), len(accs) >= 3)
r5 = moy5 / spe["cible_05"]
ligne("Compatibilité à 5 %", "Spectre moyen enveloppant le spectre cible",
      "min(moyen/cible) = %.3f à %.2f Hz" % (r5.min(), f[r5.argmin()]), r5.min() >= 1.0)
for tag in ("02", "07", "10"):
    m = np.mean([spe["s%d_%s" % (i + 1, tag)] for i in range(len(accs))], axis=0)
    r = m / spe["cible_" + tag]
    ligne("Amortissement %d %%" % int(tag), "Défauts locaux <= 10 %, sauf justification",
          "défaut max = %.1f %% à %.2f Hz" % (100 * (1 - r.min()), f[r.argmin()]),
          r.min() >= 0.90)
ligne("Pas de temps", "<= 0,01 s", "%.4f s" % dt, dt <= 0.01 + 1e-12)
ab = np.abs(rhos)
ligne("Indépendance", "|intercorrélation| <= 0,3, moyenne < 0,2",
      "max |ρ| = %.3f ; moyenne |ρ| = %.3f (%s)" % (ab.max(), ab.mean(), INTERCORR),
      ab.max() <= 0.3 and ab.mean() < 0.2)

pu.ecrire_csv(pu.chemin("Etape3", "resultats", "E3_controle.csv"),
              {"critere": crit, "exigence": exig, "resultat": resu, "respecte": ok})
for c, r, b in zip(crit, resu, ok):
    print("%-22s %-55s %s" % (c, r, b))
