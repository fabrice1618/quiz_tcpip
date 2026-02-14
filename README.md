# Quiz TCP/IP

Application Flask unifiée pour gérer plusieurs quiz avec deux modes : **entraînement** (libre) et **test** (contrôlé par le professeur avec salle d'attente).

## Installation

### 1. Cloner le dépôt

```bash
git clone <url-du-repo>
cd quiz_tcpip
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Puis éditez `.env` et modifiez les valeurs :

```bash
# Générer une SECRET_KEY sécurisée
python3 -c "import secrets; print(f'SECRET_KEY={secrets.token_hex(32)}')"

# Définir un mot de passe admin fort
ADMIN_PASSWORD=VotreMotDePasseSecurise2026!
```

### 3. Lancer avec Docker

```bash
docker compose up --build
```

L'application sera accessible sur http://localhost:5000

## Structure

- `/` — Page d'accueil listant tous les quiz
- `/binaire/` — Quiz de conversions numériques et opérations logiques
- `/reseau/` — Quiz d'adressage IP et routage
- `/admin/` — Interface d'administration (nécessite mot de passe)

## Mode test avec salle d'attente

1. Connectez-vous à `/admin/` avec le mot de passe défini dans `.env`
2. Basculez un quiz en mode "test"
3. Les étudiants qui démarrent le quiz sont mis en salle d'attente
4. Cliquez sur "Ouvrir" pour débloquer l'accès
5. Les étudiants sont automatiquement redirigés vers l'exercice 1

## Outils CLI

### Lister toutes les soumissions

```bash
python3 lister.py
```

### Consulter une soumission

```bash
python3 consulter.py binaire 123456
python3 consulter.py reseau 654321
```

## Migration des données

Si vous avez des anciennes bases de données dans `quiz_binaire/` et `quiz_reseau/` :

```bash
python3 migration.py
```

Cela fusionne les deux bases dans `data/resultats.db`.

## Sécurité

⚠️ **Important** :
- Ne committez JAMAIS le fichier `.env` (il est dans `.gitignore`)
- Changez `ADMIN_PASSWORD` avant la mise en production
- La `SECRET_KEY` doit être unique et aléatoire

## Ajouter un nouveau quiz

1. Créez `quizzes/nouveau/` avec :
   - `__init__.py` (Blueprint + routes)
   - `logic.py` (logique métier)
   - `templates/nouveau/` (templates spécifiques)
   - `static/css/quiz.css` (CSS spécifique)

2. Dans `quizzes/__init__.py`, ajoutez l'import :
   ```python
   from quizzes.nouveau import bp as bp_nouveau
   ```

3. Relancez le conteneur → le quiz apparaît automatiquement
