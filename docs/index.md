# exampy

**exampy** est une application Python en ligne de commande pour gérer une partie de **jeu de rôle** sur table — campagnes, personnages, quêtes et participations — avec persistance **MySQL** et un **shell interactif** offrant complétion Tab et historique.

Les **messages du shell et de la CLI** — aide, erreurs, invites — ainsi que les **noms de commandes** comme `campaign`, `character` ou `quest` sont en **anglais**. Pour cibler une campagne dans le shell, on privilégie le **nom exact** de la campagne ; le détail figure dans la page [Shell interactif](application/shell.md).

## Fonctions principales

| Domaine | Rôle |
|---------|------|
| **CLI** | Entrée via [Cyclopts](application/cli.md) : shell par défaut, `db-ping` pour tester MySQL. |
| **Shell** | REPL `jdr>` : [création, listes, complétion et invites](application/shell.md) branchées sur la base. |
| **Données** | [Schéma relationnel](database/schema.md) et [modules d’accès](database/modules.md) — notamment `JdrRepository` et `JdrListRepository`. |

## Par où commencer

1. [Démarrage](demarrage.md) — environnement, `.env`, initialisation SQL, `uv run exampy`.
2. [Architecture](architecture.md) — vue d’ensemble et flux des composants.
3. [Shell interactif](application/shell.md) — référence des commandes.

## Schéma d’ensemble

```mermaid
flowchart TB
  subgraph cli["CLI"]
    MAIN["main.py — Cyclopts App"]
  end
  subgraph shell["Paquet shell"]
    REPL[repl.run_shell]
    DIS[commands.dispatch]
    CMP[JdrShellCompleter]
  end
  subgraph data["Paquet database"]
    MY[MySQLDatabase]
    JW[JdrRepository]
    JL[JdrListRepository]
  end
  DB[(MySQL)]
  MAIN -->|default ou shell| REPL
  MAIN -->|db-ping| MY
  REPL --> DIS
  REPL --> CMP
  DIS --> JW
  DIS --> JL
  CMP --> JW
  JW --> MY
  JL --> MY
  MY --> DB
```
