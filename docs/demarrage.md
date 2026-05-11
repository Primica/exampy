# Démarrage

## Prérequis

- **Python** 3.14+
- **[uv](https://docs.astral.sh/uv/)** pour les dépendances et l’exécution
- Un serveur **MySQL** accessible avec une base nommée `jdr`, ou celle indiquée dans le fichier `.env`

## Installation du projet

```bash
git clone <votre-depot> exampy
cd exampy
uv sync
```

Le projet est packagé selon la clé **`tool.uv.package`** dans `pyproject.toml` : `uv sync` installe aussi le paquet local et le script **`exampy`**.

## Variables d’environnement

Créez un fichier **`.env`** à la racine du dépôt :

| Variable | Description |
|----------|-------------|
| `DB_HOST` | Hôte MySQL |
| `DB_USER` | Utilisateur |
| `DB_PASSWORD` | Mot de passe |
| `DB_NAME` | Nom de la base, par exemple `jdr` |

Le chargement du `.env` est déclenché à l’import de `database.config`, appelé depuis `main.py`.

## Initialiser le schéma SQL

Exécutez le script **`sql/init.sql`**, situé à la racine du dépôt, sur votre serveur MySQL : il crée la base `jdr` et les tables. Voir aussi la page [Schéma SQL — référence](reference/sql-init.md).

!!! warning "Destructif"
    Le script fourni commence par `DROP DATABASE IF EXISTS jdr` : à adapter si vous réutilisez une base existante.

## Lancer l’application

| Commande | Effet |
|----------|--------|
| `uv run exampy` | Shell interactif ; commande par défaut de la CLI |
| `uv run exampy shell` | Même effet que la ligne précédente |
| `uv run exampy db-ping` | Affiche la version du serveur MySQL sans ouvrir le REPL |

Les messages de **`db-ping`** et du shell — aide, erreurs, invites — sont en **anglais**.

## Documentation locale

```bash
uv run mkdocs serve
```

Puis ouvrez l’URL indiquée, en pratique `http://127.0.0.1:8000`.
