from __future__ import annotations

from typing import NamedTuple

from .repository_base import BaseJdrRepository
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


class JdrListRepository(BaseJdrRepository):
    def export_database_as_dicts(self) -> dict[str, list[dict[str, object]]]:
        with self._session() as (_conn, cur):
            cur.execute(
                """
                SELECT id, nom, maitre_du_jeu, date_creation
                FROM campagne
                ORDER BY id
                """
            )
            campagne: list[dict[str, object]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                campagne.append(
                    {
                        "id": sql_int(t[0]),
                        "nom": str(t[1]),
                        "maitre_du_jeu": str(t[2]),
                        "date_creation": t[3],
                    }
                )

            cur.execute(
                """
                SELECT id, nom, classe, niveau, points_de_vie, id_campagne
                FROM personnage
                ORDER BY id
                """
            )
            personnage: list[dict[str, object]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                personnage.append(
                    {
                        "id": sql_int(t[0]),
                        "nom": str(t[1]),
                        "classe": str(t[2]),
                        "niveau": sql_int(t[3]),
                        "points_de_vie": sql_int(t[4]),
                        "id_campagne": sql_int(t[5]),
                    }
                )

            cur.execute(
                """
                SELECT id, titre, description, statut, id_campagne
                FROM quete
                ORDER BY id
                """
            )
            quete: list[dict[str, object]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                quete.append(
                    {
                        "id": sql_int(t[0]),
                        "titre": str(t[1]),
                        "description": str(t[2]),
                        "statut": str(t[3]),
                        "id_campagne": sql_int(t[4]),
                    }
                )

            cur.execute(
                """
                SELECT id_personnage, id_quete
                FROM participation
                ORDER BY id_personnage, id_quete
                """
            )
            participation: list[dict[str, object]] = []
            for raw in cur.fetchall():
                t = row_tuple(raw)
                participation.append(
                    {
                        "id_personnage": sql_int(t[0]),
                        "id_quete": sql_int(t[1]),
                    }
                )

            return {
                "campagne": campagne,
                "personnage": personnage,
                "quete": quete,
                "participation": participation,
            }

    def list_toutes_campagnes(self) -> list[CampagneDetail]:
        with self._session() as (_conn, cur):
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

    def list_personnages_par_campagne(
        self, id_campagne: int
    ) -> list[PersonnageAvecCampagne]:
        with self._session() as (_conn, cur):
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

    def list_quetes_par_campagne(self, id_campagne: int) -> list[QueteCampagne]:
        with self._session() as (_conn, cur):
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

    def list_personnages_par_quete(self, id_quete: int) -> list[PersonnageQuete]:
        with self._session() as (_conn, cur):
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

    def list_quetes_par_personnage(self, id_personnage: int) -> list[QuetePersonnage]:
        with self._session() as (_conn, cur):
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
