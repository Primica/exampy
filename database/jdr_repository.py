from __future__ import annotations

import mysql.connector

from .mysql_db import MySQLConnectionLike, MySQLDatabase
from .sql_utils import row_tuple, sql_int


class JdrRepository:
    """Requêtes lecture / écriture sur le schéma JDR."""

    def __init__(self, db: MySQLDatabase) -> None:
        self._db = db

    def _connection(self) -> MySQLConnectionLike:
        conn = self._db.connect(quiet=True)
        if conn is None:
            raise RuntimeError("Connexion MySQL impossible.")
        return conn

    def list_campagnes(self) -> list[tuple[int, str, str]]:
        """Campagnes (id, nom, maitre_du_jeu) pour complétion / affichage."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, nom, maitre_du_jeu FROM campagne ORDER BY id LIMIT 500"
            )
            rows = cur.fetchall()
            out: list[tuple[int, str, str]] = []
            for raw in rows:
                t = row_tuple(raw)
                out.append((sql_int(t[0]), str(t[1]), str(t[2])))
            return out
        finally:
            cur.close()
            conn.close()

    def list_distinct_noms_campagne(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT DISTINCT nom FROM campagne WHERE nom LIKE %s ORDER BY nom LIMIT 50",
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_distinct_mj(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT DISTINCT maitre_du_jeu FROM campagne
                WHERE maitre_du_jeu LIKE %s ORDER BY maitre_du_jeu LIMIT 50
                """,
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_distinct_classes(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT DISTINCT classe FROM personnage
                WHERE classe LIKE %s ORDER BY classe LIMIT 50
                """,
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_distinct_noms_personnage(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT DISTINCT nom FROM personnage
                WHERE nom LIKE %s ORDER BY nom LIMIT 50
                """,
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_distinct_titres_quete(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT DISTINCT titre FROM quete
                WHERE titre LIKE %s ORDER BY titre LIMIT 50
                """,
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_distinct_statuts_quete(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT DISTINCT statut FROM quete
                WHERE statut LIKE %s ORDER BY statut LIMIT 50
                """,
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_distinct_descriptions_quete(self, prefix: str) -> list[str]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT DISTINCT description FROM quete
                WHERE description LIKE %s ORDER BY description LIMIT 30
                """,
                (f"{prefix}%",),
            )
            return [str(row_tuple(r)[0]) for r in cur.fetchall()]
        finally:
            cur.close()
            conn.close()

    def list_personnages(self, id_prefix: str) -> list[tuple[int, str]]:
        """Personnages (id, nom), filtre optionnel sur le début de l'id (texte)."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            if id_prefix:
                cur.execute(
                    """
                    SELECT id, nom FROM personnage
                    WHERE CAST(id AS CHAR) LIKE %s ORDER BY id LIMIT 100
                    """,
                    (f"{id_prefix}%",),
                )
            else:
                cur.execute(
                    "SELECT id, nom FROM personnage ORDER BY id LIMIT 100"
                )
            out: list[tuple[int, str]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append((sql_int(t[0]), str(t[1])))
            return out
        finally:
            cur.close()
            conn.close()

    def list_quetes(self, id_prefix: str) -> list[tuple[int, str]]:
        conn = self._connection()
        cur = conn.cursor()
        try:
            if id_prefix:
                cur.execute(
                    """
                    SELECT id, titre FROM quete
                    WHERE CAST(id AS CHAR) LIKE %s ORDER BY id LIMIT 100
                    """,
                    (f"{id_prefix}%",),
                )
            else:
                cur.execute("SELECT id, titre FROM quete ORDER BY id LIMIT 100")
            out: list[tuple[int, str]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append((sql_int(t[0]), str(t[1])))
            return out
        finally:
            cur.close()
            conn.close()

    def create_campagne(self, nom: str, maitre_du_jeu: str) -> int:
        """Insère une campagne. Doit précéder personnages et quêtes de cette campagne."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO campagne (nom, maitre_du_jeu) VALUES (%s, %s)",
                (nom, maitre_du_jeu),
            )
            conn.commit()
            last = cur.lastrowid
            if last is None:
                raise RuntimeError("INSERT campagne : lastrowid indisponible.")
            return int(last)
        except mysql.connector.Error:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def add_personnage(
        self,
        nom: str,
        classe: str,
        niveau: int,
        points_de_vie: int,
        id_campagne: int,
    ) -> int:
        """Ajoute un personnage à une campagne existante (FK ``id_campagne``)."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO personnage (nom, classe, niveau, points_de_vie, id_campagne)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nom, classe, niveau, points_de_vie, id_campagne),
            )
            conn.commit()
            last = cur.lastrowid
            if last is None:
                raise RuntimeError("INSERT personnage : lastrowid indisponible.")
            return int(last)
        except mysql.connector.Error:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def create_quete(
        self,
        titre: str,
        description: str,
        statut: str,
        id_campagne: int,
    ) -> int:
        """Crée une quête rattachée à une campagne existante."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO quete (titre, description, statut, id_campagne)
                VALUES (%s, %s, %s, %s)
                """,
                (titre, description, statut, id_campagne),
            )
            conn.commit()
            last = cur.lastrowid
            if last is None:
                raise RuntimeError("INSERT quete : lastrowid indisponible.")
            return int(last)
        except mysql.connector.Error:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def inscrire_participation(self, id_personnage: int, id_quete: int) -> None:
        """Inscrit un personnage à une quête (table ``participation``)."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO participation (id_personnage, id_quete) VALUES (%s, %s)",
                (id_personnage, id_quete),
            )
            conn.commit()
        except mysql.connector.Error:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
