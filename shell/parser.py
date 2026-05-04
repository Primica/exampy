"""Découpage des lignes saisies (guillemets shell via shlex)."""

from __future__ import annotations

import shlex


def parse_line(line: str) -> list[str]:
    s = line.strip()
    if not s:
        return []
    try:
        return shlex.split(s)
    except ValueError as exc:
        raise ValueError(f"Guillemets ou échappement invalides : {exc}") from exc
