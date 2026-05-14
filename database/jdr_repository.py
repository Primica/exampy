from __future__ import annotations

import mysql.connector

from .repository_base import BaseJdrRepository
from .sql_utils import row_tuple, sql_int

_DISTINCT_PREFIX_LIMITS: dict[tuple[str, str], int] = {
    ("campagne", "nom"): 50,
    ("campagne", "maitre_du_jeu"): 50,
    ("personnage", "classe"): 50,
    ("personnage", "nom"): 50,
    ("quete", "titre"): 50,
    ("quete", "statut"): 50,
    ("quete", "description"): 30,
}

_ID_LABEL_TABLE_LABEL: dict[str, str] = {
    "personnage": "nom",
    "quete": "titre",
}


class JdrRepository(BaseJdrRepository):
    def _list_distinct_by_prefix(self, table: str, column: str, prefix: str) -> list[str]:
        key = (table, column)
        limit = _DISTINCT_PREFIX_LIMITS.get(key)
        if limit is None:
            raise ValueError(f"Unknown distinct column: {table}.{column}")
        qt_table = f"`{table}`"
        qt_col = f"`{column}`"
        sql = (
            f"SELECT DISTINCT {qt_col} FROM {qt_table} "
            f"WHERE {qt_col} LIKE %s ORDER BY {qt_col} LIMIT %s"
        )
        with self._session() as (_conn, cur):
            cur.execute(sql, (f"{prefix}%", limit))
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]

    def _list_id_label_by_prefix(self, table: str, id_prefix: str) -> list[tuple[int, str]]:
        label_col = _ID_LABEL_TABLE_LABEL.get(table)
        if label_col is None:
            raise ValueError(f"Unknown id/label table: {table}")
        qt_table = f"`{table}`"
        qt_label = f"`{label_col}`"
        with self._session() as (_conn, cur):
            if id_prefix:
                cur.execute(
                    f"SELECT id, {qt_label} FROM {qt_table} "
                    "WHERE CAST(id AS CHAR) LIKE %s ORDER BY id LIMIT 100",
                    (f"{id_prefix}%",),
                )
            else:
                cur.execute(f"SELECT id, {qt_label} FROM {qt_table} ORDER BY id LIMIT 100")
            out: list[tuple[int, str]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append((sql_int(t[0]), str(t[1])))
            return out

    def _execute_insert_returning_id(
        self, sql: str, params: tuple[object, ...], error_prefix: str
    ) -> int:
        with self._session() as (conn, cur):
            try:
                cur.execute(sql, params)
                conn.commit()
                last = cur.lastrowid
                if last is None:
                    raise RuntimeError(f"{error_prefix}: lastrowid unavailable.")
                return int(last)
            except mysql.connector.Error:
                conn.rollback()
                raise

    def _execute_insert_no_row(self, sql: str, params: tuple[object, ...]) -> None:
        with self._session() as (conn, cur):
            try:
                cur.execute(sql, params)
                conn.commit()
            except mysql.connector.Error:
                conn.rollback()
                raise

    def find_campagnes_by_nom_exact(self, nom: str) -> list[tuple[int, str]]:
        with self._session() as (_conn, cur):
            cur.execute(
                """
                SELECT id, maitre_du_jeu FROM campagne
                WHERE nom = %s
                ORDER BY id
                """,
                (nom,),
            )
            out: list[tuple[int, str]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append((sql_int(t[0]), str(t[1])))
            return out

    def list_campagnes(self) -> list[tuple[int, str, str]]:
        with self._session() as (_conn, cur):
            cur.execute(
                "SELECT id, nom, maitre_du_jeu FROM campagne ORDER BY id LIMIT 500"
            )
            rows = cur.fetchall()
            out: list[tuple[int, str, str]] = []
            for raw in rows:
                t = row_tuple(raw)
                out.append((sql_int(t[0]), str(t[1]), str(t[2])))
            return out

    def list_distinct_noms_campagne(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("campagne", "nom", prefix)

    def list_distinct_mj(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("campagne", "maitre_du_jeu", prefix)

    def list_distinct_classes(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("personnage", "classe", prefix)

    def list_distinct_noms_personnage(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("personnage", "nom", prefix)

    def list_distinct_titres_quete(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("quete", "titre", prefix)

    def list_distinct_statuts_quete(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("quete", "statut", prefix)

    def list_distinct_descriptions_quete(self, prefix: str) -> list[str]:
        return self._list_distinct_by_prefix("quete", "description", prefix)

    def list_personnages(self, id_prefix: str) -> list[tuple[int, str]]:
        return self._list_id_label_by_prefix("personnage", id_prefix)

    def list_quetes(self, id_prefix: str) -> list[tuple[int, str]]:
        return self._list_id_label_by_prefix("quete", id_prefix)

    def create_campagne(self, nom: str, maitre_du_jeu: str) -> int:
        return self._execute_insert_returning_id(
            "INSERT INTO campagne (nom, maitre_du_jeu) VALUES (%s, %s)",
            (nom, maitre_du_jeu),
            "INSERT campagne",
        )

    def add_personnage(
        self,
        nom: str,
        classe: str,
        niveau: int,
        points_de_vie: int,
        id_campagne: int,
    ) -> int:
        return self._execute_insert_returning_id(
            """
            INSERT INTO personnage (nom, classe, niveau, points_de_vie, id_campagne)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nom, classe, niveau, points_de_vie, id_campagne),
            "INSERT personnage",
        )

    def create_quete(
        self,
        titre: str,
        description: str,
        statut: str,
        id_campagne: int,
    ) -> int:
        return self._execute_insert_returning_id(
            """
            INSERT INTO quete (titre, description, statut, id_campagne)
            VALUES (%s, %s, %s, %s)
            """,
            (titre, description, statut, id_campagne),
            "INSERT quete",
        )

    def inscrire_participation(self, id_personnage: int, id_quete: int) -> None:
        self._execute_insert_no_row(
            "INSERT INTO participation (id_personnage, id_quete) VALUES (%s, %s)",
            (id_personnage, id_quete),
        )
