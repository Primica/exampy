from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from .mysql_db import MySQLConnectionLike, MySQLDatabase


class BaseJdrRepository:
    def __init__(self, db: MySQLDatabase) -> None:
        self._db = db

    def _connection(self) -> MySQLConnectionLike:
        conn = self._db.connect(quiet=True)
        if conn is None:
            raise RuntimeError("Could not connect to MySQL.")
        return conn

    @contextmanager
    def _session(self) -> Iterator[tuple[MySQLConnectionLike, Any]]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            yield conn, cur
        finally:
            cur.close()
            conn.close()
