# Architecture

## Découpage des paquets Python

```mermaid
flowchart LR
  subgraph racine [Racine dépôt]
    Main[main.py]
  end
  subgraph pkgDatabase [database]
    Config[config.py]
    MySQL[mysql_db.py]
    SqlU[sql_utils.py]
    JdrW[jdr_repository.py]
    JdrR[jdr_list_repository.py]
  end
  subgraph pkgShell [shell]
    Repl[repl.py]
    Cmd[commands.py]
    Parse[parser.py]
    Comp[completer.py]
  end
  Main --> Config
  Main --> MySQL
  Main --> Repl
  Repl --> Cmd
  Repl --> Comp
  Cmd --> JdrW
  Cmd --> JdrR
  Comp --> JdrW
  JdrW --> MySQL
  JdrR --> MySQL
  JdrW --> SqlU
  JdrR --> SqlU
```

- **`main.py`** : point d’entrée Cyclopts, instancie `MySQLDatabase` et lance le shell.
- **`database`** : configuration, connexion, écritures (`JdrRepository`), lectures listes (`JdrListRepository`), utilitaires de lignes SQL (`sql_utils`).
- **`shell`** : boucle REPL (`prompt_toolkit`), dispatch des commandes, parsing `shlex`, complétion contextuelle.

## Flux d’une commande shell

```mermaid
sequenceDiagram
  participant U as Utilisateur
  participant R as repl
  participant P as parser shlex
  participant D as dispatch
  participant W as JdrRepository
  participant L as JdrListRepository
  participant M as MySQLDatabase
  U->>R: ligne saisie Tab
  R->>P: parse_line
  P-->>R: tokens
  R->>D: dispatch repo lists tokens
  alt écriture
    D->>W: create add inscrire
    W->>M: connect commit
  else liste
    D->>L: list par id
    L->>M: connect SELECT
  end
  D-->>U: tabulate ou message
```

## Connexions MySQL

Chaque méthode de dépôt ouvre une connexion, exécute la requête, valide ou annule la transaction, puis ferme la connexion. Le shell conserve **une** instance `MySQLDatabase` et **une** instance par dépôt pour toute la session ; ce n’est pas un pool partagé entre appels.

```mermaid
stateDiagram-v2
  [*] --> Connectee: connect quiet
  Connectee --> Ecriture: INSERT UPDATE
  Ecriture --> Validee: commit
  Ecriture --> Annulee: rollback erreur
  Validee --> Fermee: close
  Annulee --> Fermee: close
  Fermee --> [*]
```

## Documentation MkDocs

Les pages sous `docs/` sont assemblées par **MkDocs** avec le thème **Material** et le plugin **mermaid2** pour les diagrammes.
