# -*- coding: utf-8 -*-
"""Étape 4 — spectres de plancher moyens par cas, pics, figure.

Sorties :
  figures/E4_spectre_tete_4cas.png (+ .csv)   4 spectres moyens en tête + sol en pointillé
  figures/E4_spectre_inter_4cas.png (+ .csv)  idem au niveau intermédiaire
  resultats/E4_pics.csv                       fréquence et amplitude du pic principal
Contrôle : cas C en tête comparé aux 5,4 g de la note (écart signalé, pas corrigé).

Usage : python Etape4/E4_post.py   (après E4_spectres_plancher.export)
"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "commun"))
import post_utils as pu  # noqa: E402
from post_utils import plt  # noqa: E402

SA_NOTE_TETE = 5.4   # g, note Maurel (cas C)
XI = 0.05

d = pu.lire_csv(pu.chemin("Etape4", "resultats", "E4_spectres.csv"))
sol = pu.lire_csv(pu.chemin("Etape3", "resultats", "E3_spectres.csv"))

# regroupement : (cas, niveau) -> liste des spectres des 3 signaux
spectres = defaultdict(dict)
for cas, s, niv, xi, f, sa in zip(d["cas"], d["signal"], d["niveau"], d["amor"],
                                  d["freq_Hz"], d["sa_g"]):
    if abs(xi - XI) > 1e-6:
        continue
    spectres[(cas, niv)].setdefault(s, []).append((f, sa))

niveaux = sorted({k[1] for k in spectres}, key=lambda n: list(d["niveau"]).index(n))
niv_tete, niv_inter = niveaux[0], niveaux[-1]
cas_liste = sorted({k[0] for k in spectres})
libelles = {"A": "A — base encastrée", "B": "B — ressorts, sans amortisseurs",
            "C": "C — ressorts + amortisseurs", "D": "D — ressorts ÷ 2 + amortisseurs"}

moyennes = {}
for key, par_sig in spectres.items():
    tab = [np.array(v) for v in par_sig.values()]
    f = tab[0][:, 0]
    moyennes[key] = (f, np.mean([t[:, 1] for t in tab], axis=0))

pics = {"cas": [], "niveau": [], "f_pic_Hz": [], "sa_pic_g": []}
for niv, suffixe in ((niv_tete, "tete"), (niv_inter, "inter")):
    fig, ax = plt.subplots(figsize=(8, 5))
    colonnes = {}
    for cas in cas_liste:
        f, sa = moyennes[(cas, niv)]
        ax.plot(f, sa, lw=1.6, label=libelles.get(cas, cas))
        colonnes["freq_Hz"] = f
        colonnes["cas_%s_g" % cas] = sa
        k = int(np.argmax(sa))
        pics["cas"].append(cas); pics["niveau"].append(niv)
        pics["f_pic_Hz"].append(f[k]); pics["sa_pic_g"].append(sa[k])
    ax.plot(sol["freq_Hz"], sol["cible_05"], "k--", lw=1.2, label="Spectre de sol (cible 5 %)")
    colonnes["sol_g"] = np.interp(colonnes["freq_Hz"], sol["freq_Hz"], sol["cible_05"])
    pu.axes_spectre(ax, "Spectres de plancher moyens (3 signaux), niveau %s, ξ = 5 %%" % niv)
    ax.legend(fontsize=8)
    pu.sauver_figure(fig, "Etape4", "E4_spectre_%s_4cas" % suffixe, colonnes)

pu.ecrire_csv(pu.chemin("Etape4", "resultats", "E4_pics.csv"), pics)

for c, n, fp, sp in zip(*pics.values()):
    print("cas %s  %-6s  pic %.2f g à %.2f Hz" % (c, n, sp, fp))
sa_c = [sp for c, n, fp, sp in zip(*pics.values()) if c == "C" and n == niv_tete]
if sa_c:
    e = sa_c[0] / SA_NOTE_TETE - 1
    print("Contrôle cas C en tête : %.2f g vs %.1f g (note) -> écart %+.0f %%%s"
          % (sa_c[0], SA_NOTE_TETE, 100 * e,
             "  >>> ÉCART NOTABLE À SIGNALER" if abs(e) > 0.2 else ""))
