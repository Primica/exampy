"""Complétion contextuelle (commandes + données MySQL).

Découpe la ligne sur les espaces (sans interpréter shlex) : même limite que
pour une saisie sans guillemets ; avec guillemets, utiliser parse_line à l'exécution.
"""

from __future__ import annotations

import time
from typing import Callable, Iterable

from prompt_toolkit.completion import Completer, Completion

from database import JdrRepository

_ROOTS = ("help", "exit", "quit", "campagne", "personnage", "quete", "participation")
_SUB_CREATE = ("create",)
_SUB_ADD = ("add",)


def split_prompt(text_before_cursor: str) -> tuple[list[str], str]:
    """Mots complets avant le fragment courant, et fragment à compléter."""
    if not text_before_cursor:
        return [], ""
    ends_ws = text_before_cursor[-1].isspace()
    if ends_ws:
        head = text_before_cursor.rstrip()
        if not head:
            return [], ""
        return head.split(), ""
    head, sep, tail = text_before_cursor.rpartition(" ")
    if not sep:
        return [], tail
    return head.split(), tail


def _yield_filtered(
    choices: Iterable[str],
    prefix: str,
    *,
    meta: Callable[[str], str] | None = None,
) -> Iterable[Completion]:
    pl = prefix.lower()
    for c in sorted(choices, key=lambda x: (not x.lower().startswith(pl), x.lower())):
        if not prefix or c.lower().startswith(pl):
            yield Completion(
                c,
                start_position=-len(prefix),
                display_meta=meta(c) if meta else None,
            )


class JdrShellCompleter(Completer):
    def __init__(self, repo: JdrRepository) -> None:
        self._repo = repo
        self._campagnes_ts = 0.0
        self._campagnes_rows: list[tuple[int, str, str]] = []

    def _campagnes_cached(self) -> list[tuple[int, str, str]]:
        now = time.monotonic()
        if now - self._campagnes_ts > 1.5 or not self._campagnes_rows:
            try:
                self._campagnes_rows = self._repo.list_campagnes()
            except Exception:
                self._campagnes_rows = []
            self._campagnes_ts = now
        return self._campagnes_rows

    def get_completions(self, document, complete_event):  # noqa: ARG002
        text = document.text_before_cursor
        words, prefix = split_prompt(text)
        ends_ws = bool(text) and text[-1].isspace()

        try:
            yield from self._complete(words, prefix, ends_ws)
        except Exception:
            return

    def _complete(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if not words:
            yield from _yield_filtered(_ROOTS, prefix)
            return

        root = words[0].lower()

        if root in ("help", "exit", "quit"):
            return

        if root == "campagne":
            yield from self._complete_campagne(words, prefix, ends_ws)
            return
        if root == "personnage":
            yield from self._complete_personnage(words, prefix, ends_ws)
            return
        if root == "quete":
            yield from self._complete_quete(words, prefix, ends_ws)
            return
        if root == "participation":
            yield from self._complete_participation(words, prefix, ends_ws)
            return

        yield from _yield_filtered(_ROOTS, prefix)

    def _complete_campagne(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_CREATE, prefix)
            return
        if words[1].lower() != "create":
            return
        if len(words) == 2:
            try:
                noms = self._repo.list_distinct_noms_campagne(prefix)
            except Exception:
                noms = []
            yield from _yield_filtered(noms, prefix, meta=lambda n: "nom (existant)")
            return
        if len(words) == 3:
            try:
                mjs = self._repo.list_distinct_mj(prefix)
            except Exception:
                mjs = []
            yield from _yield_filtered(mjs, prefix, meta=lambda m: "maître du jeu")
            return

    def _complete_personnage(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_ADD, prefix)
            return
        if words[1].lower() != "add":
            return
        if len(words) == 2:
            try:
                noms = self._repo.list_distinct_noms_personnage(prefix)
            except Exception:
                noms = []
            yield from _yield_filtered(noms, prefix, meta=lambda n: "nom")
            return
        if len(words) == 3:
            try:
                classes = self._repo.list_distinct_classes(prefix)
            except Exception:
                classes = []
            yield from _yield_filtered(classes, prefix, meta=lambda c: "classe")
            return
        if len(words) == 4:
            for n in range(1, 21):
                s = str(n)
                if not prefix or s.startswith(prefix):
                    yield Completion(s, start_position=-len(prefix), display_meta="niveau")
            return
        if len(words) == 5:
            for pv in (5, 10, 15, 20, 25, 30, 40, 50):
                s = str(pv)
                if not prefix or s.startswith(prefix):
                    yield Completion(s, start_position=-len(prefix), display_meta="PV")
            return
        if (len(words) == 6 and ends_ws) or (len(words) == 6 and prefix):
            for cid, nom, mj in self._campagnes_cached():
                sid = str(cid)
                if not prefix or sid.startswith(prefix):
                    yield Completion(
                        sid,
                        start_position=-len(prefix),
                        display_meta=f"{nom} — {mj}",
                    )

    def _complete_quete(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_CREATE, prefix)
            return
        if words[1].lower() != "create":
            return
        if len(words) == 2:
            try:
                titres = self._repo.list_distinct_titres_quete(prefix)
            except Exception:
                titres = []
            yield from _yield_filtered(titres, prefix, meta=lambda t: "titre")
            return
        if len(words) == 3:
            try:
                descs = self._repo.list_distinct_descriptions_quete(prefix)
            except Exception:
                descs = []
            yield from _yield_filtered(descs, prefix, meta=lambda d: "description")
            return
        if len(words) == 4:
            try:
                stats = self._repo.list_distinct_statuts_quete(prefix)
            except Exception:
                stats = []
            defaults = ("ouverte", "en_cours", "terminee", "echec")
            merged = list(dict.fromkeys([*stats, *defaults]))
            yield from _yield_filtered(merged, prefix, meta=lambda s: "statut")
            return
        if (len(words) == 5 and ends_ws) or (len(words) == 5 and prefix):
            for cid, nom, mj in self._campagnes_cached():
                sid = str(cid)
                if not prefix or sid.startswith(prefix):
                    yield Completion(
                        sid,
                        start_position=-len(prefix),
                        display_meta=f"{nom} — {mj}",
                    )

    def _complete_participation(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_ADD, prefix)
            return
        if words[1].lower() != "add":
            return
        if len(words) == 2:
            try:
                persos = self._repo.list_personnages(prefix)
            except Exception:
                persos = []
            for pid, nom in persos:
                sid = str(pid)
                yield Completion(
                    sid,
                    start_position=-len(prefix),
                    display_meta=nom,
                )
            return
        if len(words) == 3 and ends_ws:
            try:
                quetes = self._repo.list_quetes("")
            except Exception:
                quetes = []
            for qid, titre in quetes:
                yield Completion(
                    str(qid),
                    start_position=-len(prefix),
                    display_meta=titre,
                )
            return
        if len(words) == 3 and prefix and not ends_ws:
            try:
                quetes = self._repo.list_quetes(prefix)
            except Exception:
                quetes = []
            for qid, titre in quetes:
                yield Completion(
                    str(qid),
                    start_position=-len(prefix),
                    display_meta=titre,
                )
