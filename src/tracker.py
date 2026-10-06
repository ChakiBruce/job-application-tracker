"""SQLite database operations for the job application tracker."""

from contextlib import closing
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "applications.db"


def initialize_database(database_path=DATABASE_PATH):
    """Create the database and applications table if they do not exist."""
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                application_date TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        connection.commit()

