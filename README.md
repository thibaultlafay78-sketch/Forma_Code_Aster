# Forma_Code_Aster
Exemples d'illustration de la formation Génie Civil.

Démonstrations Code_Aster du cahier des charges de B. Coq (v2.1, 06/11/2026, précisions du
16/11/2026) : six calculs qui fournissent les figures de la formation « Comprendre une note
de calcul sismique ». Code_Aster 18.1.11.

## Arborescence

| Dossier | Contenu |
|---|---|
| `commun/` | `brochette.comm` (données de la note Maurel, maillage et fonctions du modèle, inclus par les étapes 1, 2, 4 et 6) ; `post_utils.py` (CSV, style unique des figures, export PNG + SVG, spectre de contrôle) |
| `Etape1/` | Modèle brochette, calage de E sur 4,79 Hz, contrôle de masse |
| `Etape2/` | Analyse modale et quotient de Rayleigh, figure `E2_rayleigh.png` |
| `Etape3/` | 3 accélérogrammes, contrôle des critères ASN 2/01, figures `E3_signaux.png` et `E3_spectres.png` |
| `Etape4/` | Spectres de plancher pour 4 hypothèses de sol, figure `E4_spectre_tete_4cas.png` |
| `Etape5/` | Colonne 1D (DEFI_SOL_EQUI, entrées RA et CL), référence Python, figures `E5_surface_2entrees.png` et `E5_rapport.png` |
| `Etape6/` | Décollement du radier (25 appuis DIS_CHOC, DYNA_NON_LINE), figures `E6_contact.png`, `E6_moment_rotation.png`, synthèse `E6_resume.csv` |
| `note/` | Note des hypothèses retenues |
| `test/` | Cas test de prise en main (poutre 3D) |

Chaque étape contient : `.comm` + `.export` (calcul), `*_post.py` (figures), `resultats/` (CSV bruts, .mess)
et `figures/` (PNG + SVG + CSV de même nom). Les figures n'ont pas de titre (porté par la slide) ;
le CSV contient toutes les séries tracées, sans arrondi. Tailles, police, épaisseurs et couleurs
sont définies uniquement dans `commun/post_utils.py` (`STYLE`, `ROLES`).

## Exécution et contrôle

Depuis la racine du projet, dans un terminal PowerShell :

```powershell
# Tout enchaîner (≈ 1 h 15, dont ≈ 1 h pour E6) : calculs E1→E6, post-traitements, contrôle
powershell -ExecutionPolicy Bypass -File commun\tout_lancer.ps1

# Reprendre à partir d'une étape (ex. après modification de l'étape 4)
powershell -ExecutionPolicy Bypass -File commun\tout_lancer.ps1 -Depuis 4

# Une seule étape
powershell -ExecutionPolicy Bypass -File commun\lancer.ps1 Etape2\E2_modal_rayleigh.export

# Contrôle seul des résultats existants (OK / ÉCART / ABSENT)
F:\miniforge3\envs\aster\python.exe commun\controle.py
```

Les étapes dépendent les unes des autres (E1 → E2 → E4 → E6 ; E3 → E4, E5, E6) : après une
modification, relancer à partir de l'étape modifiée. Les figures PNG nécessitent
matplotlib (`conda install -n aster matplotlib`).

Mise au point de l'étape 6 : `$env:E6_RAPIDE = "3"` avant `lancer.ps1` limite les calculs à
3 s, signal 1, échelle 2 (≈ 3 min) ; retirer la variable pour le calcul complet.
