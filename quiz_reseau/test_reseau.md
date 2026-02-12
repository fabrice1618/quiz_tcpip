# Test info Atelier - Partie 2 : Réseaux

## Vue d'ensemble

Quiz interactif Flask portant sur l'adressage IP et le routage.
Deux exercices, corrigés automatiquement (sauf question 1.3 en texte libre).

---

## Exercice 1 — Adressage réseau (10 points)

### Topologie

Cinq machines connectées à un **unique switch** :

| Identification | Adresse IP    | Masque réseau   |
|----------------|---------------|-----------------|
| Ordinateur 1   | 10.1.201.37   | 255.255.224.0   |
| Ordinateur 2   | 192.168.11.3  | 255.255.0.0     |
| Ordinateur 3   | 10.1.188.37   | 255.255.224.0   |
| Rectifieuse 1  | 192.168.35.4  | 255.255.0.0     |
| Fraiseuse 1    | 10.1.214.1    | 255.255.224.0   |

### 1.1 — Calculer l'adresse réseau (5 points)

L'élève effectue un **ET logique** (AND) entre chaque octet de l'adresse IP
et le masque correspondant.

Réponses attendues :

| Machine        | Calcul (3ᵉ octet)          | Adresse réseau |
|----------------|-----------------------------|----------------|
| Ordinateur 1   | 201 AND 224 = 192           | 10.1.192.0     |
| Ordinateur 2   | 11 AND 0 = 0               | 192.168.0.0    |
| Ordinateur 3   | 188 AND 224 = 160           | 10.1.160.0     |
| Rectifieuse 1  | 35 AND 0 = 0               | 192.168.0.0    |
| Fraiseuse 1    | 214 AND 224 = 192           | 10.1.192.0     |

**Barème** : 1 point par adresse réseau correcte.

### 1.2 — Machines pouvant communiquer (5 points)

Deux machines communiquent directement si elles partagent la **même adresse
réseau**.

Groupes réseau :

- **10.1.192.0/19** : Ordinateur 1, Fraiseuse 1
- **192.168.0.0/16** : Ordinateur 2, Rectifieuse 1
- **10.1.160.0/19** : Ordinateur 3 (seul)

Réponses attendues :

| Machine        | Peut communiquer avec       |
|----------------|-----------------------------|
| Ordinateur 1   | Fraiseuse 1                 |
| Ordinateur 2   | Rectifieuse 1               |
| Ordinateur 3   | *(aucune)*                  |
| Rectifieuse 1  | Ordinateur 2                |
| Fraiseuse 1    | Ordinateur 1                |

**Barème** : 1 point par ligne entièrement correcte (toutes les bonnes
cases cochées, aucune mauvaise).

### 1.3 — Outil de diagnostique (non noté automatiquement)

Question : « En étant connecté à l'Ordinateur 1, comment vérifier si la
communication fonctionne avec la Fraiseuse 1 ? »

Réponse attendue : utiliser la commande **ping 10.1.214.1** depuis
l'Ordinateur 1.

Le texte est enregistré mais **non noté automatiquement** (correction manuelle).

---

## Exercice 2 — Routage inter-réseaux (8 points)

### Topologie

- **Routeur** avec 2 interfaces (IF0 et IF1)
- **Switch 1** connecté à l'interface 0 → Ordinateurs 1 et 2
- **Switch 2** connecté à l'interface 1 → Ordinateurs 3 et 4

### Données fournies

| Identification      | Adresse IP      | Masque réseau     |
|---------------------|-----------------|-------------------|
| Routeur interface 0 | *(à compléter)* | *(à compléter)*   |
| Routeur interface 1 | 192.168.0.254   | 255.255.255.128   |
| Ordinateur 1        | 192.168.0.1     | 255.255.255.128   |
| Ordinateur 2        | *(à compléter)* | *(à compléter)*   |
| Ordinateur 3        | *(à compléter)* | *(à compléter)*   |
| Ordinateur 4        | *(à compléter)* | *(à compléter)*   |

### Analyse des sous-réseaux

Masque /25 (255.255.255.128) → 2 sous-réseaux de 126 hôtes :

- **Sous-réseau 1** (Switch 1, IF0) : 192.168.0.0/25
  - Hôtes valides : 192.168.0.1 à 192.168.0.126
  - Adresses prises : .1 (Ordinateur 1)
- **Sous-réseau 2** (Switch 2, IF1) : 192.168.0.128/25
  - Hôtes valides : 192.168.0.129 à 192.168.0.254
  - Adresses prises : .254 (Routeur IF1)

### Contraintes de validation

| Champ               | Masque attendu    | Plage IP valide          | Exclusions |
|---------------------|-------------------|--------------------------|------------|
| Routeur IF0         | 255.255.255.128   | 192.168.0.2 – .126      | .1         |
| Ordinateur 2        | 255.255.255.128   | 192.168.0.2 – .126      | .1         |
| Ordinateur 3        | 255.255.255.128   | 192.168.0.129 – .253    | .254       |
| Ordinateur 4        | 255.255.255.128   | 192.168.0.129 – .253    | .254       |

**Barème** : 1 point par champ correct (4 IP + 4 masques = 8 points).
Les IP sont validées par contrainte (sous-réseau correct, hôte valide,
pas d'adresse déjà attribuée dans l'énoncé).

---

## Récapitulatif du barème

| Section | Points |
|---------|--------|
| 1.1 — Adresses réseau   | 5  |
| 1.2 — Communication     | 5  |
| 1.3 — Diagnostic        | — (texte libre) |
| 2 — Routage             | 8  |
| **Total**                | **18** |

---

## Architecture technique

Application Flask réutilisant le frontend de `quiz_binaire` :

- Session Flask pour stocker les réponses entre exercices
- Correction automatique à la soumission
- Stockage JSON des résultats (`resultats.json`)
- Code unique de dépôt à 6 chiffres
- Interface Bootstrap 5 avec CSS partagé
