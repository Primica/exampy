# CLI Cyclopts

L’entrée du programme est **`main.py`**. Elle instancie une application **`cyclopts.App`** nommée `exampy`. Les textes d’aide Cyclopts et les messages console associés sont en **anglais**, y compris lors d’un échec de connexion avant l’ouverture du shell.

## Commandes

```mermaid
flowchart LR
  Root[exampy]
  Default[default_cmd]
  ShellCmd[shell]
  Ping[db-ping]
  Root --> Default
  Root --> ShellCmd
  Root --> Ping
  Default --> Session[_run_shell_session]
  ShellCmd --> Session
  Ping --> Status[get_db_status]
```

| Invocation | Comportement |
|------------|----------------|
| `exampy` | Commande par défaut : vérifie une connexion MySQL puis lance le **shell** en appelant `run_shell`. |
| `exampy shell` | Identique à la ligne précédente. |
| `exampy db-ping` | Affiche la version du serveur MySQL sans ouvrir le REPL. |

## Séquence avant le shell

```mermaid
sequenceDiagram
  participant CLI as main
  participant DB as MySQLDatabase
  participant SH as run_shell
  CLI->>DB: connect quiet
  alt échec
    DB-->>CLI: None
    CLI-->>CLI: erreur connexion affichée en anglais puis arrêt
  else succès
    DB-->>CLI: connexion
    CLI->>DB: close
    CLI->>SH: run_shell db
  end
```

## Script d’entrée

Défini dans `pyproject.toml` :

```toml
[project.scripts]
exampy = "main:main"
```

Après `uv sync`, la commande **`uv run exampy`** est disponible.
