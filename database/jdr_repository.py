from __future__ import annotations
from typing import TYPE_CHECKING
import mysql.connector
from .mysql_db import MySQLDatabase

if TYPE_CHECKING:
    from mysql.connector import MySQLConnection




class JdrRepository:
    """Requêtes d'écriture sur le schéma JDR."""

    def __init__(self, db: MySQLDatabase) -> None:
        self._db = db

    def _connection(self) -> MySQLConnection:
        conn = self._db.connect(quiet=True)
        if conn is None:
            raise RuntimeError("Connexion MySQL impossible.")
        return conn

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
