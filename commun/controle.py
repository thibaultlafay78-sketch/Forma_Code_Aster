# -*- coding: utf-8 -*-
"""Contrôle automatique des résultats des étapes 1 à 5.

Compare les CSV produits aux valeurs de la note Maurel et aux critères du
cahier des charges, et affiche OK / ÉCART / ABSENT pour chaque point.
N'a pas besoin de matplotlib.

Usage : python commun/controle.py
"""
import itertools
import os
import re
import sys

import numpy as np

try:   # console Windows en cp1252 : forcer l'UTF-8 (≥, ξ, ρ…)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import post_utils as pu  # noqa: E402

lignes = []


def verif(etape, quoi, valeur, reference, ok):
    lignes.append((etape, quoi, valeur, reference, "OK" if ok else "ÉCART"))


def absent(etape, fichier):
    lignes.append((etape, "fichier " + fichier, "—", "à produire", "ABSENT"))


def fichier(etape, nom):
    p = pu.chemin(etape, "resultats", nom)
    if not os.path.exists(p):
        absent(etape, nom)
        return None
    return p


# --- Étape 1 -----------------------------------------------------------------
p = fichier("Etape1", "E1_E_retenu.csv")
if p:
    r = pu.lire_csv(p)
    E, f1, fx = r["E_MPa"][0], r["f_calee_Hz"][0], r["f_X_Hz"][0]
    verif("E1", "f1 calée (Y, ressorts)", "%.3f Hz" % f1, "4,79 Hz ± 1 %", abs(f1 / 4.79 - 1) < 0.01)
    verif("E1", "E béton", "%.0f MPa" % E, "20 000–33 000 MPa (ASN)", 20000 <= E <= 33000)
    verif("E1", "mode X (contrôle I/OX)", "%.2f Hz" % fx, "6,65 Hz ± 10 %", abs(fx / 6.65 - 1) < 0.10)
p = fichier("Etape1", "E1_masse.csv")
if p:
    m = pu.lire_csv(p)
    verif("E1", "masse totale", "%.0f t" % (m["masse_modele_kg"][0] / 1e3), "5370 t",
          abs(m["ecart_rel"][0]) < 1e-3)

# --- Étape 2 -----------------------------------------------------------------
p = fichier("Etape2", "E2_rayleigh.csv")
if p:
    r = pu.lire_csv(p)
    for c, fm, fr in zip(r["config"], r["f_calc_modes_Hz"], r["f_rayleigh_Hz"]):
        verif("E2", "Rayleigh ≥ modal (%s)" % c, "%.3f / %.3f Hz" % (fr, fm),
              "légèrement supérieur", 0 <= fr / fm - 1 < 0.10)
p = fichier("Etape2", "E2_modes.csv")
if p:
    md = pu.lire_csv(p)
    idx = [i for i, c in enumerate(md["config"]) if c == "RESSORTS"]
    for d, fnote, nom in (("DY", 4.79, "mode 1 Y"), ("DX", 6.65, "mode 2 X"), ("DZ", 13.02, "mode 3 Z")):
        i = max(idx, key=lambda k: md["frac_" + d][k])
        f = md["freq_Hz"][i]
        verif("E2", nom, "%.2f Hz (%.0f %%)" % (f, 100 * md["frac_" + d][i]),
              "%.2f Hz ± 10 %%" % fnote, abs(f / fnote - 1) < 0.10)

# --- Étape 3 -----------------------------------------------------------------
ps, pe = fichier("Etape3", "E3_signaux.csv"), fichier("Etape3", "E3_spectres.csv")
if ps and pe:
    sig, spe = pu.lire_csv(ps), pu.lire_csv(pe)
    t = sig["t_s"]
    accs = [sig[k] for k in sig if k.startswith("acc")]
    verif("E3", "nombre de signaux", str(len(accs)), "≥ 3", len(accs) >= 3)
    verif("E3", "pas de temps", "%.4f s" % (t[1] - t[0]), "≤ 0,01 s", t[1] - t[0] <= 0.01 + 1e-12)
    for tag, seuil, txt in (("05", 1.0, "enveloppe (≥ 1,00)"), ("02", 0.9, "défaut ≤ 10 %"),
                            ("07", 0.9, "défaut ≤ 10 %"), ("10", 0.9, "défaut ≤ 10 %")):
        m = np.mean([spe["s%d_%s" % (i + 1, tag)] for i in range(len(accs))], axis=0)
        r = (m / spe["cible_" + tag]).min()
        verif("E3", "spectre moyen/cible à %d %%" % int(tag), "min %.3f" % r, txt, r >= seuil - 1e-3)
    rho = np.abs([np.corrcoef(accs[i], accs[j])[0, 1]
                  for i, j in itertools.combinations(range(len(accs)), 2)])
    verif("E3", "intercorrélation", "max %.2f, moy. %.2f" % (rho.max(), rho.mean()),
          "≤ 0,3 ; moyenne < 0,2", rho.max() <= 0.3 and rho.mean() < 0.2)
    pga = max(np.abs(a).max() for a in accs) / pu.G
    verif("E3", "PGA max des signaux", "%.3f g" % pga, "≈ 0,438 g (note §V)", 0.33 <= pga <= 0.55)

# --- Étape 4 -----------------------------------------------------------------
p = fichier("Etape4", "E4_spectres.csv")
if p:
    d = pu.lire_csv(p)
    pics = {}
    for cas in "ABCD":
        sel = [(s, f, a) for c, s, n, x, f, a in zip(d["cas"], d["signal"], d["niveau"], d["amor"],
                                                   d["freq_Hz"], d["sa_g"])
               if c == cas and n == "N6" and abs(x - 0.05) < 1e-6]
        if not sel:
            continue
        f = np.array(sorted({x[1] for x in sel}))
        m = np.mean([[a for s2, ff, a in sel if s2 == s] for s in sorted({x[0] for x in sel})], axis=0)
        pics[cas] = (f[m.argmax()], m.max())
    if "C" in pics:
        fc, ac = pics["C"]
        verif("E4", "cas C, pic en tête (N6, Y)", "%.2f g à %.2f Hz" % (ac, fc),
              "5,4 g à 4,8 Hz ± 20 %", abs(ac / 5.4 - 1) < 0.20)
    if len(pics) == 4:
        ordre = pics["D"][1] < pics["C"][1] < pics["B"][1]
        verif("E4", "tendance B > C > D", " / ".join("%s %.1f g" % (c, pics[c][1]) for c in "BCD"),
              "amortissement et souplesse du sol réduisent le pic", ordre)
        verif("E4", "cas A plus raide", "%.2f Hz" % pics["A"][0], "pic > celui du cas C",
              pics["A"][0] > pics["C"][0])

# --- Étape 5 -----------------------------------------------------------------
p = fichier("Etape5", "E5.mess")
if p:
    txt = open(p, encoding="utf-8", errors="replace").read()
    it = re.findall(r"CONVERGENCE ATTEINTE NOMBRE ITERATIONS=\s*(\d+)", txt)
    verif("E5", "convergence RA / CL", "/".join(it) + " itérations", "2 calculs convergés", len(it) == 2)
p = fichier("Etape5", "E5_proprietes.csv")
if p:
    pr = pu.lire_csv(p)
    for calc in ("RA", "CL"):
        xi = [x for c, x, s in zip(pr["calcul"], pr["xi_pct"], pr["substratum"]) if c == calc and s != "OUI"]
        verif("E5", "ξ convergés (%s)" % calc, "max %.1f %%" % max(xi), "< 20 % (domaine Darendeli)", max(xi) < 20)
p = fichier("Etape5", "E5_reference_python.csv")
if p and os.path.exists(pu.chemin("Etape5", "resultats", "E5_RA_tran.txt")):
    import importlib.util
    spec = importlib.util.spec_from_file_location("e5post_parse", pu.chemin("Etape5", "E5_post.py"))
    src = open(spec.origin, encoding="utf-8").read().split("spec = {}")[0]
    g = {"__file__": spec.origin}
    exec(compile(src, spec.origin, "exec"), g)
    ref = pu.lire_csv(p)
    for calc in ("RA", "CL"):
        cour = g["lire_tableau"](pu.chemin("Etape5", "resultats", "E5_%s_tran.txt" % calc))
        t, a = cour["AX_CL"]
        sa = pu.spectre_oscillateur(t, a / pu.G, pu.FREQS, 0.05)
        band = pu.FREQS <= 10
        e = np.abs(sa[band] / ref["surface_%s_g" % calc][band] - 1).max()
        verif("E5", "Aster vs Python (%s, ≤ 10 Hz)" % calc, "écart max %.1f %%" % (100 * e),
              "< 10 %", e < 0.10)
        if calc == "CL":
            ra = np.abs(cour["AX_RA"][1]).max() / pu.G
            verif("E5", "rocher déconvolué (CL)", "PGA %.2f g" % ra, "< PGA surface, pas de divergence",
                  ra < np.abs(a).max() / pu.G)

# --- Affichage ---------------------------------------------------------------
w = [max(len(str(l[i])) for l in lignes) for i in range(5)]
for l in lignes:
    print("  ".join(str(x).ljust(w[i]) for i, x in enumerate(l)))
n_ok = sum(l[4] == "OK" for l in lignes)
print("\n%d / %d contrôles OK" % (n_ok, len(lignes)))
sys.exit(0 if n_ok == len(lignes) else 1)
