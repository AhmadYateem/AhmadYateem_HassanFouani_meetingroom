"""
MySQL connection utilities with pooled connections.

Author: Ahmad Yateem
Module: Database Connection Management
"""

import os
from contextlib import contextmanager
from typing import Optional

import mysql.connector
from mysql.connector import pooling


class MySQLConnectionPool:
    """Connection pool wrapper for MySQL."""

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


def create_pool_from_env(prefix: str = "MYSQL") -> MySQLConnectionPool:
    """
    Build a MySQL connection pool using environment variables.

    Args:
        prefix: Environment variable prefix (default: MYSQL)

    Returns:
        MySQLConnectionPool instance
    """
    host = _load_env_value(f"{prefix}_HOST", "localhost")
    port = int(_load_env_value(f"{prefix}_PORT", "3306"))
    user = _load_env_value(f"{prefix}_USER", "root")
    password = _load_env_value(f"{prefix}_PASSWORD", "password")
    database = _load_env_value(f"{prefix}_DATABASE", "smartmeetingroom")
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
    """
    Yield a pooled MySQL connection.

    Args:
        pool: MySQLConnectionPool instance

    Yields:
        MySQL connection
    """
    connection = pool.get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
