"""Boucle REPL du shell JDR (prompt_toolkit : historique + complétion)."""

from __future__ import annotations

from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from database import JdrRepository, MySQLDatabase

from .commands import dispatch
from .completer import JdrShellCompleter
from .parser import parse_line

PROMPT = "jdr> "
HISTORY_PATH = Path.home() / ".cache" / "exampy" / "shell_history"


def run_shell(db: MySQLDatabase) -> None:
    repo = JdrRepository(db)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    session = PromptSession(
        message=PROMPT,
        completer=JdrShellCompleter(repo),
        history=FileHistory(str(HISTORY_PATH)),
        complete_while_typing=True,
    )
    print("Shell JDR — Tab pour compléter (commandes + données), help / exit.")
    while True:
        try:
            line = session.prompt()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        try:
            tokens = parse_line(line)
        except ValueError as err:
            print(err)
            continue
        if not dispatch(repo, tokens):
            break
