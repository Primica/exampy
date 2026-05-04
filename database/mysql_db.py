from typing import Optional

import mysql.connector
from mysql.connector import MySQLConnection

from .config import DatabaseSettings


class MySQLDatabase:
    """Connexion MySQL et opérations de base (version serveur, etc.)."""

    def __init__(self, settings: DatabaseSettings):
        self._settings = settings

    def connect(self, *, quiet: bool = False) -> Optional[MySQLConnection]:
        try:
            connection = mysql.connector.connect(
                host=self._settings.host,
                user=self._settings.user,
                password=self._settings.password,
                database=self._settings.database,
            )
            if not quiet:
                print("Connection successful!")
            return connection
        except mysql.connector.Error as err:
            if not quiet:
                print(f"Error: {err}")
            return None

    def get_db_status(self) -> None:
        connection = self.connect()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            if version is not None:
                print(f"MySQL Server Version: {version[0]}")
            cursor.close()
            connection.close()
