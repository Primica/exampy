"""Parse input lines (shell quoting via shlex)."""

from __future__ import annotations

import shlex


def parse_line(line: str) -> list[str]:
    s = line.strip()
    if not s:
        return []
    try:
        return shlex.split(s)
    except ValueError as exc:
        raise ValueError(f"Invalid quotes or escape sequence: {exc}") from exc
