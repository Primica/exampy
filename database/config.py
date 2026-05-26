import os

import dotenv

dotenv.load_dotenv()


def getenv_required(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


class DatabaseSettings:
    __slots__ = ("host", "user", "password", "database")

    def __init__(self, host: str, user: str, password: str, database: str):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        return cls(
            host=getenv_required("MYSQL_HOST"),
            user=getenv_required("MYSQL_USER"),
            password=getenv_required("MYSQL_PASSWORD"),
            database=getenv_required("MYSQL_DB"),
        )
