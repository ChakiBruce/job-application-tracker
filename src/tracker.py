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


def add_application(company, role, application_date, status, database_path=DATABASE_PATH):
    """Save an application and return its database ID."""
    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO applications (company, role, application_date, status)
            VALUES (?, ?, ?, ?)
            """,
            (company, role, application_date, status),
        )
        connection.commit()
        return cursor.lastrowid


def get_applications(database_path=DATABASE_PATH):
    """Return saved applications in the order they were added."""
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT id, company, role, application_date, status FROM applications ORDER BY id"
        ).fetchall()


def update_application_status(application_id, status, database_path=DATABASE_PATH):
    """Update one application's status; return False if its ID is missing."""
    status = status.strip()
    if not status:
        raise ValueError("Status cannot be empty.")

    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(
            "UPDATE applications SET status = ? WHERE id = ?",
            (status, application_id),
        )
        connection.commit()
        return cursor.rowcount == 1


def search_applications(keyword="", status="", database_path=DATABASE_PATH):
    """Find company/role text matches, optionally filtered by exact status."""
    keyword = keyword.strip()
    status = status.strip()
    with closing(sqlite3.connect(database_path)) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT id, company, role, application_date, status
            FROM applications
            WHERE (instr(lower(company), lower(?)) > 0
                   OR instr(lower(role), lower(?)) > 0)
              AND (? = '' OR lower(trim(status)) = lower(?))
            ORDER BY id
            """,
            (keyword, keyword, status, status),
        ).fetchall()


def get_application_statistics(database_path=DATABASE_PATH):
    """Return the total and counts for each saved status."""
    with closing(sqlite3.connect(database_path)) as connection:
        rows = connection.execute(
            """
            SELECT status, COUNT(*) AS application_count
            FROM applications
            GROUP BY status
            ORDER BY status
            """
        ).fetchall()

    status_counts = dict(rows)
    return {
        "total": sum(status_counts.values()),
        "status_counts": status_counts,
    }
