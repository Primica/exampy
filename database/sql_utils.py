"""Utilitaires typage / accès aux cellules issues de MySQL."""

from __future__ import annotations

from typing import Any, cast


def sql_int(cell: object) -> int:
    return int(cast(Any, cell))


def row_tuple(row: object) -> tuple[Any, ...]:
    return cast(tuple[Any, ...], row)
