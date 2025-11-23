"""
MySQL connection utilities with pooled connections.
Uses mysql-connector-python to maintain a reusable pool across services.
"""

import os
from contextlib import contextmanager
from typing import Optional

import mysql.connector
from mysql.connector import pooling


class MySQLConnectionPool:
    """Lightweight connection pool wrapper for MySQL."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        pool_name: str = "smartmeetingroom_pool",
        pool_size: int = 5,
    ):
        self._pool = pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=True,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
            autocommit=False,
        )

    def get_connection(self):
        return self._pool.get_connection()


def _load_env_value(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Environment variable {key} is required for database connections.")
    return value


def create_pool_from_env(prefix: str = "DATABASE") -> MySQLConnectionPool:
    """
    Build a MySQL connection pool using environment variables.

    Expected variables (with optional prefix):
    - <PREFIX>_HOST
    - <PREFIX>_PORT
    - <PREFIX>_USER
    - <PREFIX>_PASSWORD
    - <PREFIX>_NAME
    - <PREFIX>_POOL_SIZE (optional, defaults to 5)
    """
    host = _load_env_value(f"{prefix}_HOST")
    port = int(_load_env_value(f"{prefix}_PORT", "3306"))
    user = _load_env_value(f"{prefix}_USER")
    password = _load_env_value(f"{prefix}_PASSWORD")
    database = _load_env_value(f"{prefix}_NAME")
    pool_size = int(os.getenv(f"{prefix}_POOL_SIZE", "5"))

    return MySQLConnectionPool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        pool_size=pool_size,
    )


@contextmanager
def get_connection(pool: MySQLConnectionPool):
    """Yield a pooled MySQL connection."""
    connection = pool.get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
