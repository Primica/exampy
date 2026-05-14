# Architecture

## Découpage des paquets Python

```mermaid
flowchart TB
  subgraph entry [Entrée]
    MAIN["main.py — Cyclopts App"]
  end

  subgraph shell [Paquet shell]
    REPL[repl.py]
    PAR[parser.py]
    CMD["commands.py — dispatch"]
    CMP[completer.py]
  end

  subgraph db [Paquet database]
    CFG[config.py]
    MYSQL[mysql_db.py]
    RB[repository_base.py]
    JRW[JdrRepository]
    JRL[JdrListRepository]
    SQLU[sql_utils]
  end

  DB[(MySQL)]

  MAIN -->|"default · shell"| REPL
  MAIN -->|db-ping| MYSQL
  REPL --> PAR
  REPL --> CMD
  REPL --> CMP
  PAR -->|tokens| CMD
  CMD --> JRW
  CMD --> JRL
  CMP --> JRW
  CFG -.->|"DB_* via dotenv"| MYSQL
  JRW --> RB
  JRL --> RB
  RB --> MYSQL
  JRW --> SQLU
  JRL --> SQLU
  MYSQL --> DB
```

- **`main.py`** : point d’entrée Cyclopts ; `default_cmd` et `shell` lancent le REPL, `db-ping` interroge **`MySQLDatabase`** sans ouvrir le shell.
- **`database`** : configuration, connexion **`MySQLDatabase`**, socle commun **`BaseJdrRepository`** (fichier `repository_base.py`, détaillé dans [Modules Python](database/modules.md#repository_basepy)), écritures via **`JdrRepository`**, lectures listes via **`JdrListRepository`**, utilitaires **`sql_utils`**.
- **`shell`** : boucle REPL avec **`prompt_toolkit`**, dispatch des commandes, parsing `shlex`, complétion contextuelle.

## Flux d’une commande shell

```mermaid
sequenceDiagram
    autonumber
    participant U as Utilisateur
    participant PS as PromptSession
    participant R as repl
    participant P as parser
    participant D as dispatch
    participant W as JdrRepository
    participant L as JdrListRepository
    participant M as MySQLDatabase
    U->>PS: saisie ligne Tab ou Enter
    PS->>R: ligne soumise
    R->>P: parse_line shlex
    P-->>R: tokens
    R->>D: dispatch
    opt Résolution campagne depuis nom
        D->>W: find_campagnes_by_nom_exact
        W->>M: connect SELECT
        M-->>W: lignes campagne
        W-->>D: candidats id MJ
    end
    Note over D: invites stdin si ambiguïté MJ ou numéro
    alt Écriture INSERT
        D->>W: create add inscrire
        W->>M: connect commit rollback
    else Lecture SELECT
        D->>L: listes jointes
        L->>M: connect SELECT
    end
    D-->>U: tabulate ou message
```

## Connexions MySQL

Chaque méthode de dépôt ouvre une connexion via **`BaseJdrRepository._connection()`**, exécute la requête dans un bloc **`with self._session() as (conn, cur):`** qui garantit la fermeture du curseur et de la connexion, valide ou annule la transaction pour les écritures, puis termine. Le shell conserve **une** instance `MySQLDatabase` et **une** instance par dépôt pour toute la session ; ce n’est pas un pool partagé entre appels.

```mermaid
stateDiagram-v2
    [*] --> Connectee: connect quiet
    Connectee --> Ecriture: INSERT UPDATE
    Connectee --> Lecture: SELECT lecture seule
    Ecriture --> Validee: commit
    Ecriture --> Annulee: rollback erreur
    Lecture --> Fermee: close
    Validee --> Fermee: close
    Annulee --> Fermee: close
    Fermee --> [*]
```

## Documentation MkDocs

Les pages sous `docs/` sont assemblées par **MkDocs** avec le thème **Material** et le plugin **mermaid2** pour les diagrammes.
