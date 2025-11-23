"""
Database initialization helpers for applying the MySQL schema.
"""

from pathlib import Path
from typing import Optional

from database.connection import MySQLConnectionPool, get_connection


def _read_sql_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def initialize_schema(pool: MySQLConnectionPool, schema_path: Optional[Path] = None):
    """
    Apply the schema SQL to the target database using the provided connection pool.

    Args:
        pool: Active MySQLConnectionPool
        schema_path: Optional override path to the schema.sql file
    """
    resolved_path = schema_path or Path(__file__).parent / "schema.sql"
    sql = _read_sql_file(resolved_path)

    with get_connection(pool) as conn:
        cursor = conn.cursor()
        for statement in filter(None, (part.strip() for part in sql.split(";"))):
            cursor.execute(statement)
        cursor.close()
