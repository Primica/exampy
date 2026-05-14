# Modules Python — paquet `database`

## Vue d’ensemble

```mermaid
flowchart TB
  subgraph configuration [Configuration]
    GE[getenv_required]
    DS[DatabaseSettings.from_env]
    GE --> DS
  end
  subgraph connexion [mysql_db]
    MD[MySQLDatabase]
  end
  subgraph socle [repository_base]
    BR[BaseJdrRepository]
  end
  subgraph depots [Dépôts]
    JR[JdrRepository]
    JL[JdrListRepository]
  end
  subgraph utilitaire [sql_utils]
    SU[row_tuple sql_int]
  end
  DS -.->|instanciation| MD
  JR --> BR
  JL --> BR
  BR --> MD
  JR --> SU
  JL --> SU
```

## `config.py`

- Charge **`python-dotenv`** au chargement du module.
- **`DatabaseSettings`** : `host`, `user`, `password`, `database` construits depuis les variables `DB_*`.
- **`getenv_required`** : lève une erreur si une variable est absente ; le message d’erreur est en anglais.

## `mysql_db.py`

- **`MySQLDatabase`** : encapsule `mysql.connector.connect` avec le type de retour **`MySQLConnectionLike`**, union de **`PooledMySQLConnection`** et **`MySQLConnectionAbstract`**.
- **`connect(quiet=False)`** : en mode silencieux, pas de message console ; utilisé par les dépôts et le pré-contrôle shell.
- **`get_db_status()`** : `SELECT VERSION()` pour la commande CLI `db-ping`.

<a id="repository_basepy"></a>

## `repository_base.py`

- **`BaseJdrRepository`** : classe de base pour les dépôts JDR. Elle reçoit une instance **`MySQLDatabase`**, expose **`_connection()`** (connexion `quiet=True`, erreur explicite si la connexion est `None`) et un gestionnaire de contexte **`_session()`** qui rend le couple **`(conn, cur)`** et assure dans un `finally` la fermeture du curseur puis de la connexion.
- **`JdrRepository`** et **`JdrListRepository`** héritent de cette classe : toutes les requêtes passent par **`with self._session() as (conn, cur):`** (ou une méthode interne qui l’utilise), ce qui évite la duplication du motif ouverture / fermeture.

## `sql_utils.py`

- **`row_tuple`** / **`sql_int`** : adaptation des lignes renvoyées par le connecteur aux types attendus par **pyright**, pour des cellules SQL souvent typées de façon large.

## `jdr_repository.py` — écriture et lectures pour le shell

### API publique inchangée

| Méthode | Table |
|---------|--------|
| `create_campagne` | `campagne` |
| `add_personnage` | `personnage` |
| `create_quete` | `quete` |
| `inscrire_participation` | `participation` |
| `find_campagnes_by_nom_exact` | `campagne` — lecture des identifiants pour un `nom` exact |

Méthodes auxiliaires pour la **complétion** du shell : `list_campagnes`, listes distinctes `list_distinct_*`, `list_personnages`, `list_quetes` avec préfixe d’id.

**Résolution de campagne côté shell** : le shell appelle `find_campagnes_by_nom_exact(nom)`, qui renvoie la liste des couples id et `maitre_du_jeu` pour un **nom exact** de campagne. Plusieurs lignes sont possibles si le même `nom` existe pour des MJ différents, conformément à la contrainte d’unicité composite en base.

### Détails d’implémentation (référence)

- Les requêtes **`SELECT DISTINCT … LIKE`** partagées par les `list_distinct_*` sont centralisées dans **`_list_distinct_by_prefix`**, avec une **liste blanche** `(table, colonne) → LIMIT` : seuls les couples prévus peuvent être interrogés ; les identifiants SQL sont passés via des noms contrôlés (backticks).
- **`list_personnages`** et **`list_quetes`** délèguent à **`_list_id_label_by_prefix`**, pour laquelle seules les tables **`personnage`** et **`quete`** sont autorisées, avec les colonnes libellé attendues (`nom` / `titre`).
- Les INSERT avec **`lastrowid`** utilisent **`_execute_insert_returning_id`** ; **`inscrire_participation`** utilise **`_execute_insert_no_row`** (même gestion commit / rollback sur erreur **`mysql.connector.Error`**).

## `jdr_list_repository.py` — lectures structurées

**`JdrListRepository`** hérite de **`BaseJdrRepository`** et n’expose que des lectures ; chaque méthode utilise **`_session()`** comme le dépôt d’écriture.

Retours typés en **`NamedTuple`** :

| Méthode | Rôle |
|---------|------|
| `list_toutes_campagnes` | Toutes les campagnes, avec `date_creation` |
| `list_personnages_par_campagne` | Jointure `personnage` ⋈ `campagne` |
| `list_quetes_par_campagne` | Quêtes d’une campagne : titre, description, statut |
| `list_personnages_par_quete` | Jointure `participation` ⋈ `personnage` |
| `list_quetes_par_personnage` | Jointure `participation` ⋈ `quete` |

## Export public

Le paquet **`database`** réexporte les classes et types utiles via `database/__init__.py`. **`BaseJdrRepository`** n’est pas réexporté : il sert de socle interne au paquet. Voir `database/__init__.py` dans le dépôt pour la liste exacte des symboles publics.
