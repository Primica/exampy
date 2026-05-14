from __future__ import annotations

from cyclopts import App

from database import DatabaseSettings, MySQLDatabase
from shell import run_shell

app = App(
    name="exampy",
    help="RPG helper: interactive shell and database connectivity checks.",
)


def _make_db() -> MySQLDatabase:
    return MySQLDatabase(DatabaseSettings.from_env())


def _run_shell_session() -> None:
    db = _make_db()
    conn = db.connect(quiet=True)
    if conn is None:
        print("Could not connect to MySQL. Check .env and that the server is running.")
        return
    conn.close()
    run_shell(db)


@app.default
def default_cmd() -> None:
    _run_shell_session()


@app.command
def shell() -> None:
    _run_shell_session()


@app.command
def db_ping() -> None:
    db = _make_db()
    db.get_db_status()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
