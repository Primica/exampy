"""Lecture structurée : listes et jointures sur le schéma JDR."""

from __future__ import annotations

from typing import NamedTuple

from .mysql_db import MySQLConnectionLike, MySQLDatabase
from .sql_utils import row_tuple, sql_int


class CampagneDetail(NamedTuple):
    id: int
    nom: str
    maitre_du_jeu: str
    date_creation: str


class PersonnageAvecCampagne(NamedTuple):
    id: int
    nom: str
    classe: str
    niveau: int
    points_de_vie: int
    id_campagne: int
    nom_campagne: str


class QueteCampagne(NamedTuple):
    id: int
    titre: str
    description: str
    statut: str
    id_campagne: int


class PersonnageQuete(NamedTuple):
    id: int
    nom: str
    classe: str
    niveau: int
    points_de_vie: int


class QuetePersonnage(NamedTuple):
    id: int
    titre: str
    statut: str
    id_campagne: int


class JdrListRepository:
    """Requêtes de liste (jointures lecture seule)."""

    def __init__(self, db: MySQLDatabase) -> None:
        self._db = db

    def _connection(self) -> MySQLConnectionLike:
        conn = self._db.connect(quiet=True)
        if conn is None:
            raise RuntimeError("Connexion MySQL impossible.")
        return conn

    def list_toutes_campagnes(self) -> list[CampagneDetail]:
        """Toutes les campagnes, avec date de création."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, nom, maitre_du_jeu, date_creation
                FROM campagne
                ORDER BY id
                """
            )
            out: list[CampagneDetail] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append(
                    CampagneDetail(
                        sql_int(t[0]),
                        str(t[1]),
                        str(t[2]),
                        str(t[3]),
                    )
                )
            return out
        finally:
            cur.close()
            conn.close()

    def list_personnages_par_campagne(
        self, id_campagne: int
    ) -> list[PersonnageAvecCampagne]:
        """Personnages d'une campagne (jointure ``personnage`` ⇢ ``campagne``)."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.id, p.nom, p.classe, p.niveau, p.points_de_vie,
                       p.id_campagne, c.nom AS nom_campagne
                FROM personnage p
                INNER JOIN campagne c ON c.id = p.id_campagne
                WHERE p.id_campagne = %s
                ORDER BY p.id
                """,
                (id_campagne,),
            )
            out: list[PersonnageAvecCampagne] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append(
                    PersonnageAvecCampagne(
                        sql_int(t[0]),
                        str(t[1]),
                        str(t[2]),
                        sql_int(t[3]),
                        sql_int(t[4]),
                        sql_int(t[5]),
                        str(t[6]),
                    )
                )
            return out
        finally:
            cur.close()
            conn.close()

    def list_quetes_par_campagne(self, id_campagne: int) -> list[QueteCampagne]:
        """Toutes les quêtes d'une campagne (titre, description, statut)."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, titre, description, statut, id_campagne
                FROM quete
                WHERE id_campagne = %s
                ORDER BY id
                """,
                (id_campagne,),
            )
            out: list[QueteCampagne] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append(
                    QueteCampagne(
                        sql_int(t[0]),
                        str(t[1]),
                        str(t[2]),
                        str(t[3]),
                        sql_int(t[4]),
                    )
                )
            return out
        finally:
            cur.close()
            conn.close()

    def list_personnages_par_quete(self, id_quete: int) -> list[PersonnageQuete]:
        """Personnages inscrits à une quête (``participation`` ⇢ ``personnage``)."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT p.id, p.nom, p.classe, p.niveau, p.points_de_vie
                FROM participation part
                INNER JOIN personnage p ON p.id = part.id_personnage
                WHERE part.id_quete = %s
                ORDER BY p.nom, p.id
                """,
                (id_quete,),
            )
            out: list[PersonnageQuete] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append(
                    PersonnageQuete(
                        sql_int(t[0]),
                        str(t[1]),
                        str(t[2]),
                        sql_int(t[3]),
                        sql_int(t[4]),
                    )
                )
            return out
        finally:
            cur.close()
            conn.close()

    def list_quetes_par_personnage(self, id_personnage: int) -> list[QuetePersonnage]:
        """Quêtes d'un personnage via ``participation`` ⇢ ``quete``."""
        conn = self._connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT q.id, q.titre, q.statut, q.id_campagne
                FROM participation part
                INNER JOIN quete q ON q.id = part.id_quete
                WHERE part.id_personnage = %s
                ORDER BY q.id
                """,
                (id_personnage,),
            )
            out: list[QuetePersonnage] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                out.append(
                    QuetePersonnage(
                        sql_int(t[0]),
                        str(t[1]),
                        str(t[2]),
                        sql_int(t[3]),
                    )
                )
            return out
        finally:
            cur.close()
            conn.close()
