# Démonstrations Code_Aster : note des hypothèses retenues

*Projet : formation « Comprendre une note de calcul sismique ». Version du 10/11/2026.*
*Destinataire : Basile Coq.*

Cette note liste les hypothèses prises pour les cinq calculs, en particulier celles que la note de Ph. Maurel (SEIS-SPEC001-A-06-2010, 10 juin 2010) ne fixe pas, et résume les résultats bruts. Les points marqués **[À VALIDER]** restent à trancher.

Les résultats illustrent des tendances. Ils ne valident ni l'ouvrage ni la note Maurel. Le modèle brochette ne représente pas les amplifications locales des planchers, comme l'auteur le signale lui-même (§II).

---

## 0. Environnement et conventions

| Point | Choix |
|---|---|
| Version Code_Aster | 18.1.11 (développement, Windows, environnement conda `aster`) **[À VALIDER]** |
| Vérification des mots-clés | Sur le catalogue des commandes installé (`code_aster/Cata/Commands`) |
| Lancement | `commun/lancer.ps1 <étape>/<fichier>.export` (le `run_aster.bat` du conda n'active pas l'environnement ; répertoire temporaire sur E:) |
| Unités | SI dans les .comm (N, m, kg, s, Pa) ; figures en g et en Hz |
| Spectres | ξ = 5 % sauf indication contraire ; 200 fréquences logarithmiques de 0,5 à 100 Hz |
| Échange entre étapes | Fichiers CSV déclarés dans les .export (E1 → E2, E4 ; E2 → E4 ; E3 → E4, E5) |
| Modèle commun | `commun/brochette.comm`, lu par les étapes 1, 2 et 4 |

**Écarts techniques avec le cahier des charges.**
- `K_TR_D_L` et `A_TR_D_L` s'appliquent aux mailles SEG2. Sur la maille POI1 du radier, le calcul utilise `K_TR_D_N` et `A_TR_D_N`, avec les mêmes valeurs.
- `INCLUDE` lit le fichier inclus dans l'encodage local (cp1252 sous Windows) et échoue sur les fichiers UTF-8. Le modèle commun est donc exécuté par une lecture UTF-8 explicite.
- Le fichier `Modèle_brochette.export` est encodé en cp1252, faute de quoi run_aster ne trouve pas le .comm au nom accentué. Un nom sans accent éviterait ce piège.

---

## 1. Étape 1 : modèle brochette et calage du module

### Données relevées (note Maurel §II, figure 2 et tableau des raideurs)

| Nœud | z (m) | Masse (t) | Tronçon sous le nœud | S (m²) | I/OX (m⁴) | I/OY (m⁴) |
|---|---|---|---|---|---|---|
| 1 (radier, ressorts) | 0 | 1251 | — | — | — | — |
| 2 | 6 | 1269 | 12 | 51,28 | 3261 | 1029 |
| 3 | 12 | 1144 | 23 | 54,69 | 3405 | 1053 |
| 4 | 18 | 720 | 34 | 30,54 | 1938 | 582 |
| 5 | 24 | 635 | 45 | 23,40 | 1658 | 554 |
| 6 | 30 | 351 | 56 | 18,10 | 1233 | 421 |

Sol : raideurs X 3,45E4, Y 3,80E4, Z 4,10E4 MN/m ; RX 1,90E6, RY 5,10E6, RZ 3,80E6 MN·m/rad. Amortissements de 25 % en X et Y, 30 % en Z, 10 % en rotation. Béton : ρ = 2500 kg/m³ et η = 7 %. Le module de Young n'est pas donné.

### Hypothèses

| # | Hypothèse | Justification |
|---|---|---|
| H1.1 | **I/OX gouverne la flexion selon X, I/OY la flexion selon Y** (I/OX → IY, I/OY → IZ dans Code_Aster, repère local y = Y global) | Seule lecture cohérente avec la note §III : mode 1 en Y (direction faible, 12 m) à 4,79 Hz, mode 2 en X à 6,65 Hz. Contrôle : le modèle donne 6,91 Hz en X |
| H1.2 | JX = IY + IZ (torsion non donnée) | Sans effet sur les résultats horizontaux |
| H1.3 | Coefficients de cisaillement AY = AZ = 1 | Non donnés ; l'effet est absorbé par le calage de E |
| H1.4 | RHO = 0 dans le béton : masses condensées aux nœuds | Les masses de la figure 2 sont issues du modèle 3D |
| H1.5 | Masses de niveau en DIS_T, sans inertie de rotation | Cahier (M_T_D_N). Le mode de torsion à 14,6 Hz de la note est donc absent |
| H1.6 | Masse M1 portée par le discret DIS_TR du radier. Inerties de rotation en plaque mince 24 × 12 m (X selon 24 m) | Non données |
| H1.7 | Calage sur ressorts, direction Y (mode 1) | Note §III : la base modale inclut l'ISS (amortissement modal de 10 % au mode 1) |
| H1.8 | ν béton = 0,2 ; calage itératif E ← E·(f_cible/f)², arrêté à 0,1 % | Cahier |

### Résultats

- **E calé = 25 140 MPa**, pour f₁ = 4,794 Hz (écart de +0,08 %). Cette valeur est dans la plage du guide ASN 2/01, annexe 1 (20 000 à 33 000 MPa, voiles fissurés A.1.2) **[À VALIDER : acceptation du module calé]**.
- Masse du modèle (POST_ELEM) : 5370 t, égale à la somme des masses de la note.
- Avec le même E, le premier mode en base encastrée est à 7,67 Hz.

---

## 2. Étape 2 : analyse modale et quotient de Rayleigh

| # | Hypothèse |
|---|---|
| H2.1 | Modes calculés jusqu'à 33 Hz, au moins 10 modes |
| H2.2 | Mode fondamental = mode de plus grande masse effective en Y |
| H2.3 | Déformée de Rayleigh : forces Fᵢ = mᵢ·g en Y, radier compris (base sur ressorts) |
| H2.4 | Référence : Chopra, *Dynamics of Structures*, ch. 8 **[À VALIDER : §]** |

### Résultats

| Mode | Note Maurel | Modèle Code_Aster |
|---|---|---|
| 1 (Y) | 4,79 Hz, 60,1 % | 4,79 Hz, 61,7 % |
| 2 (X) | 6,65 Hz, 67,0 % | 6,91 Hz, 72,0 % |
| 3 (Z) | 13,02 Hz, 99,9 % | 12,53 Hz, 98,1 % |
| 4 (torsion) | 14,6 Hz | absent (H1.5) |
| Y second mode | 16,3 Hz, 32,6 % | 17,11 Hz, 32,7 % |
| X second mode | 17,2 Hz, 30,4 % | 18,94 Hz, 26,0 % |
| Y troisième mode | 29,5 Hz, 6,1 % | 32,97 Hz, 5,2 % |

| Configuration | CALC_MODES | Rayleigh | Écart |
|---|---|---|---|
| Base sur ressorts | 4,794 Hz | 4,898 Hz | +2,2 % |
| Base encastrée | 7,667 Hz | 7,831 Hz | +2,1 % |

Le quotient de Rayleigh majore la fréquence exacte, comme attendu. Le sol abaisse la fréquence fondamentale de 37 % (7,67 → 4,79 Hz).

---

## 3. Étape 3 : accélérogrammes

| # | Hypothèse | Statut |
|---|---|---|
| H3.1 | EC8 type 2, sol B, décret du 23/06/2009 : S = 1,35 ; TB = 0,05 s ; TC = 0,25 s ; TD = 2,5 s | **Confirmé** par la note §IV, figure 3 |
| H3.2 | Asymptote a_g·S = 0,333 g (a_g = 2,42 m/s²), plateau à 5 % = 0,83 g | **Confirmé** (note §IV) |
| H3.3 | Passage entre amortissements : η = √(10/(5+ξ%)) ≥ 0,55 | Cohérent avec la note (pic de 0,995 g à 2 % retrouvé) ; **[À VALIDER]** pour la formation |
| H3.4 | Durée de phase forte : 10 s, modulation GAMMA. Signaux de 30 s (la note : 20 s) | **[À VALIDER]** |
| H3.5 | GENE_ACCE_SEISME, SPEC_MEDIANE, dt = 0,005 s (note §IV), 3 tirages, graine 200, filtre 0,05 Hz, 20 itérations, cible définie de 0,1 à 100 Hz | Choix. Sans l'extension sous 0,5 Hz, déficit de 17 % à 0,5 Hz |
| H3.6 | Ligne de base : si le déplacement final dépasse 1 cm, CORR_ACCE par POLYNOME ou FILTRAGE (0,1 Hz). On garde la méthode qui réduit le plus la dérive, et seulement si elle l'améliore | La méthode POLYNOME aggravait un signal (1,9 → 4,1 cm) |
| H3.7 | **Mise à l'échelle commune de 1,057** des 3 signaux, pour que le spectre moyen à 5 % enveloppe la cible | Le générateur cale le spectre *médian* : avec 3 tirages, le spectre moyen restait localement 5 % sous la cible (vers 4,2 Hz) |
| H3.8 | Intercorrélation : coefficient de Pearson global ; critère « moyenne < 0,2 » sur la moyenne des \|ρ\| | **[À VALIDER]** |

### Tableau de contrôle (guide ASN 2/01 §2.2.3)

| Critère | Exigence | Résultat | Respecté |
|---|---|---|---|
| Nombre de signaux | ≥ 3 | 3 | oui |
| Compatibilité à 5 % | spectre moyen enveloppant | min(moyen/cible) = 1,000 | oui |
| Amortissement 2 % | défaut ≤ 10 % | 6,2 % (à 100 Hz) | oui |
| Amortissement 7 % | défaut ≤ 10 % | 2,8 % (4,1 Hz) | oui |
| Amortissement 10 % | défaut ≤ 10 % | 7,5 % (2,4 Hz) | oui |
| Pas de temps | ≤ 0,01 s | 0,005 s | oui |
| Indépendance | \|ρ\| ≤ 0,3, moyenne < 0,2 | max 0,18 ; moyenne 0,13 | oui |

PGA : 0,41 à 0,46 g, contre 0,438 g pour le signal de la note. Le dépassement de la cible atteint +42 % vers 1 Hz, ce qui va dans le sens de la sécurité.

**Contrôle indépendant.** Un Newmark Python recalcule les spectres SPEC_OSCI à moins de 1 % près jusqu'à 20 Hz. L'écart atteint 9 % à 100 Hz, ce qui est attendu : avec dt = 0,005 s, 100 Hz est la fréquence de Nyquist.

---

## 4. Étape 4 : spectres de plancher

| # | Hypothèse | Statut |
|---|---|---|
| H4.1 | Rayleigh béton à 7 % sur f₁ = 4,79 Hz et f₂ = 17,11 Hz (premier mode où la masse cumulée en Y atteint 90 %) : AMOR_ALPHA = 1,017E-3 s, AMOR_BETA = 3,294 s⁻¹ | Mêmes coefficients pour les 4 cas |
| H4.2 | **C construite explicitement** : C = AMOR_ALPHA·K_structure + AMOR_BETA·M + C_sol | Voir l'encadré ci-dessous |
| H4.3 | Amortisseurs de sol : cᵢ = 2ξᵢKᵢ/ω₁, avec ω₁ = 2π × 4,79 Hz et ξ de la note | Choix, à discuter. Donne un amortissement de 13 % au mode 1 du cas C, contre 10 % dans la note |
| H4.4 | Cas D : amortisseurs du cas C conservés | **[À VALIDER]** |
| H4.5 | Cas A : base encastrée simulée par des raideurs ×10⁴ | Évite des termes de Lagrange dans C |
| H4.6 | Direction Y (comme la note §VI-VII), chargement −M·Δ·a_g(t). Accélération absolue = relative + a_g | Signe de CALC_CHAR_SEISME vérifié |
| H4.7 | Newmark accélération moyenne, dt = 0,005 s ; sorties au nœud 6 (tête) et au nœud 4 (niveau intermédiaire) | Cahier |
| H4.8 | Amortissement d'équipement | **[À VALIDER]** : à fournir |

> **Point d'attention Code_Aster.** Les éléments discrets ignorent AMOR_ALPHA et AMOR_BETA du matériau : la matrice AMOR_MECA est nulle, vérifié en 18.1.11. Comme toute la masse est portée par les discrets (RHO = 0), le Rayleigh « standard » n'apporte que la part αK des poutres, soit environ 2 à 3 % au lieu de 7 %. Une première exécution donnait ainsi 31 g en tête dans le cas B. La matrice C est donc assemblée explicitement : le terme αK ne porte que sur la structure, pas sur les ressorts de sol. Contrôle par décroissance libre : ξ(mode 1) = 6,1 % dans le cas B, 13 % dans le cas C.

### Résultats (spectres moyens des 3 signaux, 5 %, direction Y)

| Cas | Tête (nœud 6) : pic | Nœud 4 : pic | Tête à 100 Hz |
|---|---|---|---|
| A — base encastrée | 6,89 g à 7,56 Hz | 3,39 g à 7,56 Hz | 1,40 g |
| B — ressorts, sans amortisseurs | 8,21 g à 5,07 Hz (second pic 7,36 g à 16,8 Hz) | 4,50 g | 1,97 g |
| C — ressorts + amortisseurs | **5,34 g à 5,21 Hz** | 2,92 g à 5,07 Hz | 1,17 g |
| D — ressorts ÷ 2 + amortisseurs | 2,92 g à 3,88 Hz | 1,81 g à 3,88 Hz | 0,93 g |

**Contrôle cas C.** On obtient 5,34 g à 5,2 Hz, contre 5,4 g à 4,8 Hz dans la note (calcul transitoire, §VII) et 5,2 g à 5,1 Hz par FSG (§VI), soit un écart de −1 %. La note obtient 1,3 g à 50 Hz ; le modèle donne 1,17 g à 100 Hz.

---

## 5. Étape 5 : colonne 1D

| # | Hypothèse |
|---|---|
| H5.1 | Profil didactique du cahier, non modifié. 11 sous-couches, puis le substratum en dernière COUCHE (5 m) |
| H5.2 | Courbes de Darendeli tabulées par couche (sous-couche centrale), appliquées à toutes les sous-couches de la couche |
| H5.3 | γ et D convertis de % en fraction. AMOR_HYST = 2·D (convention de DEFI_SOL_EQUI) |
| H5.4 | E = 2ρVs²(1+ν), ν = 0,33 pour le sol et 0,25 pour le substratum. Seul G compte en ondes SH |
| H5.5 | Substratum linéaire, ξ = 1 %. γ_eff = 0,65·γ_max, au plus 20 itérations, tolérance de 2 % |
| H5.6 | Signal n° 1 de l'étape 3 (PGA 0,455 g), maillage automatique de la macro |

**Troisième calcul.** En 18.1.11, DEFI_SOL_EQUI n'accepte que `LIEU_SIGNAL = AFFLEURANT` ou `CHAMP_LIBRE`. La lecture « en profondeur, base rigide » est donc fournie par le script indépendant `E5_reference_python.py` (matrices de transfert de type SHAKE), qui traite aussi RA et CL pour comparaison.

**Observation sur le profil, sans modification.** Le cahier annonce une fréquence de site 1/(4Σhᵢ/Vsᵢ) ≈ 3,3 Hz. La fonction de transfert élastique exacte culmine vers **4,1 Hz** (base rigide) et **4,2 Hz** (rocher affleurant). Le code a été vérifié sur une couche homogène : 2,857 Hz obtenus pour 2,857 Hz théoriques. L'approximation en temps de parcours sous-estime f₀ quand la raideur croît avec la profondeur.

### Résultats

| Lecture du signal | Itérations | PGA en surface | PGA au rocher affleurant | G/Gmax mini | ξ maxi |
|---|---|---|---|---|---|
| RA : signal au rocher affleurant | 8 | 1,02 g | 0,45 g (signal) | 0,22 (limon, 1,5–3 m) | 15,7 % |
| CL : signal en surface (déconvolution) | 4 | 0,46 g (signal) | 0,21 g (déconvolué) | 0,58 | 7,8 % |
| Profondeur, base rigide (Python seul) | 9 | 1,09 g | — | 0,17 | 17,4 % |

Spectres en surface à 5 % : le rapport RA/CL vaut 1,35 à 1 Hz, 2,9 vers 3 Hz, environ 2,2 de 5 à 10 Hz et 1,5 à 20 Hz. **Un même signal, lu comme mouvement au rocher plutôt qu'en surface, donne en surface un spectre 2 à 3 fois plus fort sur la plage des fréquences du bâtiment.** C'est le message de la slide.

**Contrôle croisé.** DEFI_SOL_EQUI et la référence Python concordent à moins de 1 % sous 7 Hz et à moins de 8 % jusqu'à 20 Hz (spectres en surface, lectures RA et CL).

**Déconvolution (H5.7).** Sans coupure, le mouvement déconvolué au rocher divergeait à haute fréquence (74 g). Le calcul CL utilise donc FREQ_COUP = 30 Hz. Le signal de surface filtré a alors un PGA de 0,475 g, contre 0,455 g pour le signal brut.

---

## 6. Points ouverts (à trancher avec Basile)

- [ ] Version de Code_Aster (proposée : 18.1.11)
- [x] Configuration associée à 4,79 Hz : ressorts, direction Y (note §III)
- [ ] Module du béton : acceptation du module calé de 25 140 MPa
- [ ] Durée de phase forte (proposée : 10 s)
- [ ] Règle de passage d'un amortissement à l'autre (proposée : η de l'EC8, cohérente avec la note)
- [ ] Définition de l'intercorrélation (proposée : coefficient global)
- [ ] Mise à l'échelle de 1,057 des signaux pour l'enveloppe à 5 % (ajouté)
- [ ] Amortisseurs du cas D (proposés : valeurs de la note)
- [ ] Formule des amortisseurs de sol, H4.3 (ajouté)
- [ ] Amortissement d'équipement
- [ ] Validation de la colonne didactique, y compris l'observation sur f₀
- [ ] Diffusion : la note Maurel est citée comme source, n'est pas diffusée, et aucune de ses figures n'est reprise
