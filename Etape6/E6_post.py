# -*- coding: utf-8 -*-
"""Étape 6 — décollement du radier : figures et tableau de synthèse.

Entrée : resultats/E6_series.csv (une ligne par calcul et par instant), écrit
par E6_decollement.comm.

Sorties :
  figures/E6_contact.png (+ .svg, .csv)
      surface en contact (%) au cours du temps (0–12 s tracés, 30 s dans le
      CSV), échelle 1 en haut et échelle 2 en bas, pour le
      signal le plus sévère (surface en contact minimale à l'échelle 2 en
      contact unilatéral) ; en tirets, la surface comprimée du modèle à
      contact bilatéral ; seuils 90 % et 70 % en pointillé ;
  figures/E6_moment_rotation.png (+ .svg, .csv)
      moment de renversement en fonction de la rotation du radier, échelle 2,
      même signal, contact bilatéral et unilatéral ;
  figures/E6_resume.csv
      par modèle, signal et échelle : surface minimale en contact, moment
      maximal, rotation maximale, accélération maximale en tête ;
  resultats/E6_controle_dt.csv
      contrôle du pas de temps (RCC-CW DA 5310) : écarts sur M max et θ max.

Usage : python Etape6/E6_post.py   (après E6_decollement.export)
"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402

DT = 0.005
SEUILS = (90.0, 70.0)                   # % de surface en contact (cahier)
NOM_MODELE = {"LIN": "Contact bilatéral (linéaire)", "NL": "Contact unilatéral (DIS_CHOC)"}

d = pu.lire_csv(pu.chemin("Etape6", "resultats", "E6_series.csv"))
calc = defaultdict(lambda: defaultdict(list))
champs = ("t_s", "pct_contact", "moment_Nm", "rotation_rad", "acc_tete_abs_g")
for i in range(len(d["t_s"])):
    cle = (d["modele"][i], int(d["signal"][i]), float(d["echelle"][i]), round(float(d["dt_s"][i]), 6))
    for c in champs:
        calc[cle][c].append(d[c][i])
calc = {k: {c: np.array(v) for c, v in s.items()} for k, s in calc.items()}


def sur_grille(s, dt=DT):
    """Instants de la liste de calcul seulement (les éventuels instants issus
    d'une subdivision automatique sont écartés pour les figures)."""
    n = np.round(s["t_s"] / dt)
    ok = np.abs(s["t_s"] - n * dt) < 1e-7
    return {c: v[ok] for c, v in s.items()}


# --- Tableau de synthèse --------------------------------------------------------
resume = defaultdict(list)
for (m, js, ech, dt), s in sorted(calc.items()):
    resume["modele"].append(m)
    resume["signal"].append(js)
    resume["echelle"].append(ech)
    resume["dt_s"].append(dt)
    resume["surface_min_contact_pct"].append(s["pct_contact"].min())
    resume["moment_max_MNm"].append(np.abs(s["moment_Nm"]).max() / 1e6)
    resume["rotation_max_mrad"].append(np.abs(s["rotation_rad"]).max() * 1e3)
    resume["acc_tete_max_g"].append(np.abs(s["acc_tete_abs_g"]).max())
pu.ecrire_csv(pu.chemin("Etape6", "figures", "E6_resume.csv"), resume)

print("%-4s %-3s %-4s %-7s %10s %10s %10s %8s" % ("mod", "sig", "éch", "dt", "contact%",
                                                  "M MN·m", "θ mrad", "a g"))
for r in zip(*resume.values()):
    print("%-4s %-3d %-4.0f %-7.4f %10.0f %10.1f %10.3f %8.2f" % r)

# --- Signal présenté : surface en contact minimale, NL, échelle 2 ----------------
sigs = sorted({k[1] for k in calc})
js = min(sigs, key=lambda j: calc[("NL", j, 2.0, DT)]["pct_contact"].min())
print("Signal présenté sur les figures : %d" % js)

# --- Figure E6_contact ---------------------------------------------------------
# Deux panneaux (échelle 1 en haut, échelle 2 en bas), zoom sur la phase forte ;
# le CSV contient les 30 s.
T_ZOOM = 12.0
fig, axs = pu.nouvelle_figure(2, 1, figsize=(8, 6), sharex=True)
colonnes = {}
for k, (ax, ech) in enumerate(zip(axs, (1.0, 2.0))):
    s_nl = sur_grille(calc[("NL", js, ech, DT)])
    s_li = sur_grille(calc[("LIN", js, ech, DT)])
    if not np.allclose(s_li["t_s"], s_nl["t_s"]):
        raise ValueError("grilles de temps différentes entre LIN et NL")
    colonnes["t_s"] = s_nl["t_s"]
    ax.plot(s_nl["t_s"], s_nl["pct_contact"],
            **pu.trait("serie", color=pu.couleur(1), lw=1.0, label="Contact unilatéral : surface en contact"))
    ax.plot(s_li["t_s"], s_li["pct_contact"],
            **pu.trait("lineaire", color=pu.couleur(0), label="Contact bilatéral : surface comprimée"))
    colonnes["contact_unilateral_x%d_pct" % ech] = s_nl["pct_contact"]
    colonnes["comprime_bilateral_x%d_pct" % ech] = s_li["pct_contact"]
    for s_ in SEUILS:
        ax.axhline(s_, **pu.trait("seuil"))
    ax.plot([], [], **pu.trait("seuil", label="Seuils 90 % et 70 %"))
    ax.set_ylabel("Surface en contact (%)")
    ax.set_ylim(0, 105)
    ax.set_xlim(0, T_ZOOM)
    ax.legend(loc="lower right", title="Signal %d, séisme × %d" % (js, ech))
for s_ in SEUILS:
    colonnes["seuil_%d_pct" % s_] = np.full_like(colonnes["t_s"], s_)
axs[-1].set_xlabel("Temps (s)")
pu.sauver_figure(fig, "Etape6", "E6_contact", colonnes)

# --- Figure E6_moment_rotation (échelle 2) -------------------------------------
fig, ax = pu.nouvelle_figure(figsize=(7, 5))
colonnes = {}
for k, m in enumerate(("LIN", "NL")):
    s = sur_grille(calc[(m, js, 2.0, DT)])
    colonnes["t_s"] = s["t_s"]
    ax.plot(s["rotation_rad"] * 1e3, s["moment_Nm"] / 1e6,
            **pu.trait("serie", color=pu.couleur(k), lw=0.8, label=NOM_MODELE[m]))
    colonnes["rotation_%s_mrad" % m] = s["rotation_rad"] * 1e3
    colonnes["moment_%s_MNm" % m] = s["moment_Nm"] / 1e6
ax.set_xlabel("Rotation du radier (mrad)")
ax.set_ylabel("Moment de renversement (MN·m)")
ax.axhline(0.0, **pu.trait("unite"))
ax.axvline(0.0, **pu.trait("unite"))
ax.legend(loc="upper left", title="Signal %d, séisme × 2" % js)
pu.sauver_figure(fig, "Etape6", "E6_moment_rotation", colonnes)

# --- Contrôle du pas de temps (RCC-CW DA 5310) ---------------------------------
ctrl = [k for k in calc if k[3] != DT]
if ctrl:
    m, j, ech, dt2 = ctrl[0]
    a, b = calc[(m, j, ech, DT)], calc[(m, j, ech, dt2)]
    lignes = defaultdict(list)
    for nom, col, f in (("moment_max", "moment_Nm", 1e-6), ("rotation_max", "rotation_rad", 1e3)):
        va, vb = np.abs(a[col]).max(), np.abs(b[col]).max()
        lignes["grandeur"].append(nom)
        lignes["dt_%g_s" % DT].append(va * f)
        lignes["dt_%g_s" % dt2].append(vb * f)
        lignes["ecart_rel"].append(vb / va - 1.0)
        lignes["respecte_10pct"].append("OUI" if abs(vb / va - 1.0) < 0.10 else "NON")
        print("contrôle dt (%s, signal %d, × %d) : %s %.4g -> %.4g (écart %+.1f %%)"
              % (m, j, ech, nom, va * f, vb * f, 100 * (vb / va - 1)))
    pu.ecrire_csv(pu.chemin("Etape6", "resultats", "E6_controle_dt.csv"), lignes)
