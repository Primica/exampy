# Démarrage

## Prérequis

- **Python** 3.14+
- **[uv](https://docs.astral.sh/uv/)** pour les dépendances et l’exécution
- Un serveur **MySQL** accessible avec une base `jdr` (ou le nom défini dans `.env`)

## Installation du projet

```bash
git clone <votre-depot> exampy
cd exampy
uv sync
```

Le projet est packagé (`tool.uv.package = true`) : `uv sync` installe aussi le paquet local et le script **`exampy`**.

## Variables d’environnement

Créez un fichier **`.env`** à la racine du dépôt :

| Variable | Description |
|----------|-------------|
| `DB_HOST` | Hôte MySQL |
| `DB_USER` | Utilisateur |
| `DB_PASSWORD` | Mot de passe |
| `DB_NAME` | Nom de la base (ex. `jdr`) |

Le chargement du `.env` est déclenché à l’import de `database.config` (appelé depuis `main.py`).

## Initialiser le schéma SQL

Exécutez le script **`sql/init.sql`** (à la racine du dépôt) sur votre serveur MySQL (création de la base `jdr` et des tables). Voir aussi la page [Schéma SQL (référence)](reference/sql-init.md).

!!! warning "Destructif"
    Le script fourni commence par `DROP DATABASE IF EXISTS jdr` : à adapter si vous réutilisez une base existante.

## Lancer l’application

| Commande | Effet |
|----------|--------|
| `uv run exampy` | Shell interactif (commande par défaut) |
| `uv run exampy shell` | Idem |
| `uv run exampy db-ping` | Affiche la version du serveur MySQL |

## Documentation locale

```bash
uv run mkdocs serve
```

Puis ouvrez l’URL indiquée (souvent `http://127.0.0.1:8000`).
