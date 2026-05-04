# Modules Python (`database`)

## Vue d’ensemble

```mermaid
flowchart TB
  subgraph config [Configuration]
    DBSettings[DatabaseSettings.from_env]
    Getenv[getenv_required]
  end
  subgraph conn [Connexion]
    MySQLDB[MySQLDatabase.connect]
  end
  subgraph write [Écriture]
    JdrW[JdrRepository]
  end
  subgraph read [Lecture listes]
    JdrR[JdrListRepository]
  end
  subgraph util [Utilitaires]
    SqlU[sql_utils row_tuple sql_int]
  end
  DBSettings --> MySQLDB
  JdrW --> MySQLDB
  JdrR --> MySQLDB
  JdrW --> SqlU
  JdrR --> SqlU
```

## `config.py`

- Charge **`python-dotenv`** au chargement du module.
- **`DatabaseSettings`** : `host`, `user`, `password`, `database` construits depuis les variables `DB_*`.
- **`getenv_required`** : lève une erreur si une variable est absente.

## `mysql_db.py`

- **`MySQLDatabase`** : encapsule `mysql.connector.connect` avec le type de retour **`MySQLConnectionLike`** (`PooledMySQLConnection | MySQLConnectionAbstract`).
- **`connect(quiet=False)`** : en mode silencieux, pas de message console (utilisé par les dépôts et le pré-contrôle shell).
- **`get_db_status()`** : `SELECT VERSION()` pour la commande CLI `db-ping`.

## `sql_utils.py`

- **`row_tuple`** / **`sql_int`** : adaptation des lignes renvoyées par le connecteur aux types attendus par **pyright** (cellules SQL typées largement).

## `jdr_repository.py` — écriture

| Méthode | Table |
|---------|--------|
| `create_campagne` | `campagne` |
| `add_personnage` | `personnage` |
| `create_quete` | `quete` |
| `inscrire_participation` | `participation` |

Méthodes auxiliaires pour la **complétion** du shell : `list_campagnes`, listes distinctes (`list_distinct_*`), `list_personnages`, `list_quetes` avec préfixe d’id.

## `jdr_list_repository.py` — lectures structurées

Retours typés en **`NamedTuple`** :

| Méthode | Rôle |
|---------|------|
| `list_toutes_campagnes` | Toutes les campagnes (+ `date_creation`) |
| `list_personnages_par_campagne` | Jointure `personnage` ⋈ `campagne` |
| `list_quetes_par_campagne` | Quêtes d’une campagne (titre, description, statut) |
| `list_personnages_par_quete` | Jointure `participation` ⋈ `personnage` |
| `list_quetes_par_personnage` | Jointure `participation` ⋈ `quete` |

## Export public

Le paquet **`database`** réexporte les classes et types utiles via `database/__init__.py` (voir le fichier dans le dépôt).
