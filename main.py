"""Point d'entrée CLI (Cyclopts)."""

from __future__ import annotations

import database.config  # noqa: F401 — charge le .env au démarrage

from cyclopts import App

from database import DatabaseSettings, MySQLDatabase
from shell import run_shell

app = App(name="exampy", help="Outil JDR : shell interactif et tests de base de données.")


def _make_db() -> MySQLDatabase:
    return MySQLDatabase(DatabaseSettings.from_env())


def _run_shell_session() -> None:
    db = _make_db()
    conn = db.connect(quiet=True)
    if conn is None:
        print("Connexion MySQL impossible. Vérifiez le .env et le serveur.")
        return
    conn.close()
    run_shell(db)


@app.default
def default_cmd() -> None:
    """Démarre le shell interactif (comportement sans sous-commande)."""
    _run_shell_session()


@app.command
def shell() -> None:
    """Démarre le shell interactif JDR."""
    _run_shell_session()


@app.command
def db_ping() -> None:
    """Affiche la version du serveur MySQL (test de connexion)."""
    db = _make_db()
    db.get_db_status()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
