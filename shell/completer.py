from __future__ import annotations

import shlex
import time
from typing import Callable, Iterable, TypeVar

from prompt_toolkit.completion import Completer, Completion

from database import JdrRepository

_ROOTS = (
    "help",
    "exit",
    "quit",
    "clear",
    "export",
    "campaign",
    "character",
    "quest",
    "participation",
)
_SUB_ADD = ("add",)
_SUB_CAMPAIGN = ("create", "list")
_SUB_CHARACTER = ("add", "list", "quests")
_SUB_QUEST = ("create", "list", "characters")

T = TypeVar("T")


def _safe_call(fn: Callable[[], T], default: T) -> T:
    try:
        return fn()
    except Exception:
        return default


def _yield_int_id_completions(
    rows: list[tuple[int, str]],
    prefix: str,
) -> Iterable[Completion]:
    for eid, meta in rows:
        sid = str(eid)
        yield Completion(
            sid,
            start_position=-len(prefix),
            display_meta=meta,
        )


def split_prompt(text_before_cursor: str) -> tuple[list[str], str]:
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


def _yield_campaign_names(
    rows: list[tuple[int, str, str]],
    prefix: str,
) -> Iterable[Completion]:
    pl = prefix.lower()
    if prefix.isdigit():
        for cid, nom, mj in sorted(rows, key=lambda x: x[0]):
            sid = str(cid)
            if sid.startswith(prefix):
                yield Completion(
                    sid,
                    start_position=-len(prefix),
                    display_meta=f"{nom} · {mj}",
                )
        return
    for _cid, nom, mj in sorted(rows, key=lambda x: x[1].lower()):
        if pl and not nom.lower().startswith(pl):
            continue
        quoted = shlex.quote(nom)
        yield Completion(
            quoted,
            start_position=-len(prefix),
            display_meta=mj,
        )


class JdrShellCompleter(Completer):
    def __init__(self, repo: JdrRepository) -> None:
        self._repo = repo
        self._campagnes_ts = 0.0
        self._campagnes_rows: list[tuple[int, str, str]] = []

    def _campagnes_cached(self) -> list[tuple[int, str, str]]:
        now = time.monotonic()
        if now - self._campagnes_ts > 1.5 or not self._campagnes_rows:
            self._campagnes_rows = _safe_call(
                lambda: self._repo.list_campagnes(), []
            )
            self._campagnes_ts = now
        return self._campagnes_rows

    def get_completions(self, document, complete_event):
        _ = complete_event
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

        if root in ("help", "exit", "quit", "clear", "export"):
            return

        if root == "campaign":
            yield from self._complete_campaign(words, prefix, ends_ws)
            return
        if root == "character":
            yield from self._complete_character(words, prefix, ends_ws)
            return
        if root == "quest":
            yield from self._complete_quest(words, prefix, ends_ws)
            return
        if root == "participation":
            yield from self._complete_participation(words, prefix, ends_ws)
            return

        yield from _yield_filtered(_ROOTS, prefix)

    def _complete_campaign(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_CAMPAIGN, prefix)
            return
        sub = words[1].lower()
        if sub == "list":
            return
        if sub != "create":
            return
        if len(words) == 2:
            noms = _safe_call(
                lambda: self._repo.list_distinct_noms_campagne(prefix), []
            )
            yield from _yield_filtered(noms, prefix, meta=lambda n: "name (existing)")
            return
        if len(words) == 3:
            mjs = _safe_call(lambda: self._repo.list_distinct_mj(prefix), [])
            yield from _yield_filtered(mjs, prefix, meta=lambda m: "dungeon master")
            return

    def _complete_character(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_CHARACTER, prefix)
            return
        sub = words[1].lower()
        if sub == "list":
            if (len(words) == 2 and ends_ws) or (len(words) == 2 and prefix):
                yield from _yield_campaign_names(self._campagnes_cached(), prefix)
            return
        if sub == "quests":
            if (len(words) == 2 and ends_ws) or (len(words) == 2 and prefix):
                persos = _safe_call(lambda: self._repo.list_personnages(prefix), [])
                yield from _yield_int_id_completions(persos, prefix)
            return
        if sub != "add":
            return
        if len(words) == 2:
            noms = _safe_call(
                lambda: self._repo.list_distinct_noms_personnage(prefix), []
            )
            yield from _yield_filtered(noms, prefix, meta=lambda n: "name")
            return
        if len(words) == 3:
            classes = _safe_call(lambda: self._repo.list_distinct_classes(prefix), [])
            yield from _yield_filtered(classes, prefix, meta=lambda c: "class")
            return
        if len(words) == 4:
            for n in range(1, 21):
                s = str(n)
                if not prefix or s.startswith(prefix):
                    yield Completion(s, start_position=-len(prefix), display_meta="level")
            return
        if len(words) == 5:
            for pv in (5, 10, 15, 20, 25, 30, 40, 50):
                s = str(pv)
                if not prefix or s.startswith(prefix):
                    yield Completion(s, start_position=-len(prefix), display_meta="HP")
            return
        if (len(words) == 6 and ends_ws) or (len(words) == 6 and prefix):
            yield from _yield_campaign_names(self._campagnes_cached(), prefix)

    def _complete_quest(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_QUEST, prefix)
            return
        sub = words[1].lower()
        if sub == "list":
            if (len(words) == 2 and ends_ws) or (len(words) == 2 and prefix):
                yield from _yield_campaign_names(self._campagnes_cached(), prefix)
            return
        if sub == "characters":
            if (len(words) == 2 and ends_ws) or (len(words) == 2 and prefix):
                quetes = _safe_call(lambda: self._repo.list_quetes(prefix), [])
                yield from _yield_int_id_completions(quetes, prefix)
            return
        if sub != "create":
            return
        if len(words) == 2:
            titres = _safe_call(lambda: self._repo.list_distinct_titres_quete(prefix), [])
            yield from _yield_filtered(titres, prefix, meta=lambda t: "title")
            return
        if len(words) == 3:
            descs = _safe_call(
                lambda: self._repo.list_distinct_descriptions_quete(prefix), []
            )
            yield from _yield_filtered(descs, prefix, meta=lambda d: "description")
            return
        if len(words) == 4:
            stats = _safe_call(lambda: self._repo.list_distinct_statuts_quete(prefix), [])
            defaults = ("ouverte", "en_cours", "terminee", "echec")
            merged = list(dict.fromkeys([*stats, *defaults]))
            yield from _yield_filtered(merged, prefix, meta=lambda s: "status")
            return
        if (len(words) == 5 and ends_ws) or (len(words) == 5 and prefix):
            yield from _yield_campaign_names(self._campagnes_cached(), prefix)

    def _complete_participation(
        self, words: list[str], prefix: str, ends_ws: bool
    ) -> Iterable[Completion]:
        if len(words) == 1:
            yield from _yield_filtered(_SUB_ADD, prefix)
            return
        if words[1].lower() != "add":
            return
        if len(words) == 2:
            persos = _safe_call(lambda: self._repo.list_personnages(prefix), [])
            yield from _yield_int_id_completions(persos, prefix)
            return
        if len(words) == 3:
            id_prefix = "" if ends_ws else prefix
            quetes = _safe_call(lambda: self._repo.list_quetes(id_prefix), [])
            yield from _yield_int_id_completions(quetes, prefix)
            return
