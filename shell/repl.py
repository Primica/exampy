"""Boucle REPL du shell JDR.

Pour historique et complétion, on pourra remplacer ``input()`` par prompt_toolkit.
"""

from __future__ import annotations

from database import JdrRepository, MySQLDatabase

from .commands import dispatch
from .parser import parse_line

PROMPT = "jdr> "


def run_shell(db: MySQLDatabase) -> None:
    repo = JdrRepository(db)
    print("Shell JDR — tapez help, exit ou quit.")
    while True:
        try:
            line = input(PROMPT)
        except EOFError:
            print()
            break
        try:
            tokens = parse_line(line)
        except ValueError as err:
            print(err)
            continue
        if not dispatch(repo, tokens):
            break
