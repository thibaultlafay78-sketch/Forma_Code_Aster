# -*- coding: utf-8 -*-
"""Utilitaires de post-traitement communs aux étapes 1 à 5 (hors Code_Aster).

Conventions du cahier des charges :
  - figures en g et en Hz, axes titrés avec unités ;
  - spectres à 5 % sauf indication contraire, fréquences log 0,5–100 Hz, 200 points ;
  - une figure = un PNG nommé d'après l'étape et le cas, données dans un CSV du même nom.
"""
import csv
import os

import numpy as np

try:   # matplotlib n'est nécessaire que pour les figures (pas pour controle.py)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402
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
    return "%.6e" % v if isinstance(v, (float, np.floating)) else v


def sauver_figure(fig, etape, nom, colonnes):
    """Enregistre <etape>/figures/<nom>.png et le CSV de données associé."""
    dossier = chemin(etape, "figures")
    os.makedirs(dossier, exist_ok=True)
    fig.tight_layout()
    fig.savefig(os.path.join(dossier, nom + ".png"), dpi=200)
    ecrire_csv(os.path.join(dossier, nom + ".csv"), colonnes)
    plt.close(fig)
    print("figure :", os.path.join(dossier, nom + ".png"))


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


def axes_spectre(ax, titre=None):
    ax.set_xscale("log")
    ax.set_xlabel("Fréquence (Hz)")
    ax.set_ylabel("Accélération spectrale (g)")
    ax.grid(True, which="both", alpha=0.3)
    if titre:
        ax.set_title(titre)
