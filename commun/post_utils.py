# -*- coding: utf-8 -*-
"""Utilitaires de post-traitement communs aux étapes 1 à 6 (hors Code_Aster).

Conventions du cahier des charges (v2.1, précisions du 16/11/2026) :
  - figures en g et en Hz, axes titrés avec unités, légende ; PAS de titre dans
    l'image (le titre est porté par la slide) ;
  - spectres à 5 % sauf indication contraire, fréquences log 0,5–100 Hz, 200 points ;
  - une figure = un PNG + un SVG nommés d'après l'étape et le cas ;
  - CSV du même nom contenant TOUTES les séries tracées (cible, seuils,
    références compris), une colonne par série, unité dans l'en-tête, point
    décimal, sans arrondi ;
  - style (police, tailles, épaisseurs, couleurs) défini UNIQUEMENT ici :
    les scripts d'étape appellent trait(<rôle>) et n'écrivent aucune couleur.
    Pas d'effort sur les couleurs : la mise aux couleurs de la formation sera
    faite ensuite à partir des CSV.
"""
import csv
import os

import numpy as np

# -----------------------------------------------------------------------------
# Style des figures : seul endroit où tailles, police, épaisseurs et couleurs
# sont définies.
# -----------------------------------------------------------------------------
STYLE = {
    "police": "DejaVu Sans",
    "taille_police": 10,        # axes, graduations
    "taille_legende": 8,
    "taille_etiquette": 8,      # valeurs écrites sur les barres
    "figsize": (8.0, 5.0),      # pouces
    "dpi": 200,
    "grille_alpha": 0.3,
}

# Rôle d'une série -> propriétés de trait. Couleurs : cycle matplotlib par
# défaut ("C0", "C1"…) et gris/noir pour les séries de référence.
ROLES = {
    "serie":      dict(lw=1.6),                              # courbe principale (couleur du cycle)
    "signal":     dict(lw=0.7, alpha=0.6),                   # signaux individuels
    "temporel":   dict(lw=0.6),                              # accélérogramme
    "moyenne":    dict(lw=1.8, color="black"),               # moyenne de plusieurs signaux
    "cible":      dict(lw=1.8, ls="--", color="C3"),         # spectre cible
    "sol":        dict(lw=1.2, ls="--", color="black"),      # spectre de sol
    "controle":   dict(lw=1.2, ls=":", color="grey"),        # recalcul indépendant
    "reference":  dict(lw=1.0, ls=":"),                      # référence (couleur du cycle)
    "rapport":    dict(lw=1.6, color="black"),               # rapport de deux spectres
    "seuil":      dict(lw=1.0, ls="--", color="grey"),       # seuil horizontal
    "unite":      dict(lw=0.6, color="black"),               # ligne y = 1
    "lineaire":   dict(lw=1.0, ls="--"),                     # modèle linéaire (couleur du cycle)
}


def couleur(i):
    """i-ème couleur du cycle par défaut (pour associer deux séries)."""
    return "C%d" % (i % 10)


def trait(role, **surcharge):
    """Propriétés de trait d'un rôle, éventuellement complétées (label, color=couleur(i))."""
    kw = dict(ROLES[role])
    kw.update(surcharge)
    return kw


try:   # matplotlib n'est nécessaire que pour les figures (pas pour controle.py)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402

    matplotlib.rcParams.update({
        "font.family": STYLE["police"],
        "font.size": STYLE["taille_police"],
        "legend.fontsize": STYLE["taille_legende"],
        "figure.figsize": STYLE["figsize"],
        "savefig.dpi": STYLE["dpi"],
        "axes.grid": True,
        "grid.alpha": STYLE["grille_alpha"],
        "svg.fonttype": "none",          # texte éditable dans le SVG
    })
except ImportError:
    plt = None

G = 9.81
FREQS = np.logspace(np.log10(0.5), np.log10(100.0), 200)

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chemin(etape, *morceaux):
    return os.path.join(RACINE, etape, *morceaux)


def lire_csv(path):
    """CSV -> dict de colonnes (float si possible)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    entetes, data = rows[0], {h: [] for h in rows[0]}
    for r in rows[1:]:
        if not r:
            continue
        for h, v in zip(entetes, r):
            try:
                data[h].append(float(v))
            except ValueError:
                data[h].append(v)
    return {h: (np.array(v) if all(isinstance(x, float) for x in v) else v)
            for h, v in data.items()}


def ecrire_csv(path, colonnes):
    """colonnes : dict ordonné {entete: liste/array}."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cles = list(colonnes)
    n = max(len(colonnes[c]) for c in cles)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cles)
        for i in range(n):
            w.writerow([_fmt(colonnes[c][i]) if i < len(colonnes[c]) else "" for c in cles])


def _fmt(v):
    """Flottants sans arrondi (représentation exacte la plus courte, point
    décimal) ; NaN -> case vide."""
    if isinstance(v, (float, np.floating)):
        return "" if np.isnan(v) else repr(float(v))
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def nouvelle_figure(nrows=1, ncols=1, **kw):
    """plt.subplots avec la taille par défaut du style."""
    return plt.subplots(nrows, ncols, figsize=kw.pop("figsize", STYLE["figsize"]), **kw)


def sauver_figure(fig, etape, nom, colonnes):
    """Enregistre <etape>/figures/<nom>.png, <nom>.svg et le CSV de données
    associé. Refuse une figure titrée (le titre est porté par la slide)."""
    for ax in fig.axes:
        if ax.get_title():
            raise ValueError("%s : pas de titre dans l'image (cahier v2.1)" % nom)
    if fig._suptitle is not None and fig._suptitle.get_text():
        raise ValueError("%s : pas de titre dans l'image (cahier v2.1)" % nom)
    dossier = chemin(etape, "figures")
    os.makedirs(dossier, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(dossier, nom + ".png"), dpi=STYLE["dpi"])
    fig.savefig(os.path.join(dossier, nom + ".svg"))
    ecrire_csv(os.path.join(dossier, nom + ".csv"), colonnes)
    plt.close(fig)
    print("figure :", os.path.join(dossier, nom + ".png"), "(+ .svg, .csv)")


def spectre_oscillateur(t, acc, freqs=FREQS, xi=0.05):
    """Spectre de pseudo-accélération ω²·max|u|, même unité que acc.
    Newmark accélération moyenne, signal rééchantillonné (interpolation
    linéaire) à dt <= 1/(20·fmax). Contrôle indépendant de SPEC_OSCI."""
    freqs = np.asarray(freqs, dtype=float)
    dt0 = t[1] - t[0]
    n_sub = max(1, int(np.ceil(dt0 * 20.0 * freqs.max())))
    dt = dt0 / n_sub
    tf = np.arange(0.0, t[-1] + 0.5 * dt, dt)
    p = -np.interp(tf, t, acc)
    w = 2 * np.pi * freqs
    c, k = 2 * xi * w, w ** 2
    beta, gam = 0.25, 0.5
    kh = k + gam * c / (beta * dt) + 1.0 / (beta * dt ** 2)
    A = 1.0 / (beta * dt) + gam * c / beta
    B = 1.0 / (2 * beta) + dt * (gam / (2 * beta) - 1.0) * c
    u = np.zeros_like(w)
    v = np.zeros_like(w)
    a = p[0] - c * v - k * u
    umax = np.zeros_like(w)
    for i in range(len(p) - 1):
        du = ((p[i + 1] - p[i]) + A * v + B * a) / kh
        dv = gam / (beta * dt) * du - gam / beta * v + dt * (1 - gam / (2 * beta)) * a
        da = du / (beta * dt ** 2) - v / (beta * dt) - a / (2 * beta)
        u, v, a = u + du, v + dv, a + da
        np.maximum(umax, np.abs(u), out=umax)
    return k * umax


def axes_spectre(ax, ylabel="Accélération spectrale (g)"):
    ax.set_xscale("log")
    ax.set_xlabel("Fréquence (Hz)")
    ax.set_ylabel(ylabel)
    ax.grid(True, which="both", alpha=STYLE["grille_alpha"])
