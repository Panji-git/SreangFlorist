"""
Database connection and session management for Sreang Florist.
SQLite with strict Foreign Key constraints and Row Factory.
"""

import os
import sqlite3
from pathlib import Path
from typing import Generator

# Root project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database file location (defaults to project root sreang_florist.db)
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "sreang_florist.db"))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Strict foreign key pragma and Row factory are applied.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency that yields a database connection and ensures it is closed.
    """
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db(schema_file: Path = SCHEMA_PATH) -> None:
    """
    Initializes the database schema from the schema.sql file.
    """
    conn = get_db_connection()
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print(f"Initializing database at: {DB_PATH}")
    init_db()
    print("Database schema successfully initialized.")
