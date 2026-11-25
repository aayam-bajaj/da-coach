"""db.py - SQLite helpers for the Data Analyst prep app."""

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta

DB_PATH = "progress.db"


@contextmanager
def get_connection(db_path=DB_PATH):
    """Open a connection, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=DB_PATH):
    """Create progress.db and its tables if they do not exist yet."""
    with get_connection(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS completed_modules (
                module_id    TEXT PRIMARY KEY,
                completed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS study_logs (
                date         TEXT PRIMARY KEY,
                hours_logged REAL NOT NULL CHECK (hours_logged BETWEEN 0 AND 24),
                notes        TEXT NOT NULL DEFAULT ''
            );
            """
        )


def toggle_module(module_id, db_path=DB_PATH):
    """Mark a module complete, or incomplete if it already was.

    Returns True if the module is complete after the call, False otherwise.
    """
    with get_connection(db_path) as conn:
        removed = conn.execute(
            "DELETE FROM completed_modules WHERE module_id = ?", (module_id,)
        ).rowcount
        if removed:
            return False
        conn.execute(
            "INSERT INTO completed_modules (module_id, completed_at) VALUES (?, ?)",
            (module_id, datetime.now().isoformat(timespec="seconds")),
        )
        return True


def log_study_hours(hours, notes="", log_date=None, db_path=DB_PATH):
    """Add study hours to a day (defaults to today).

    Hours accumulate if the day already has an entry. Non-empty notes
    replace the existing notes for that day.
    """
    if hours <= 0 or hours > 24:
        raise ValueError("hours must be greater than 0 and at most 24")
    day = (log_date or date.today()).isoformat()
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO study_logs (date, hours_logged, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                hours_logged = MIN(24, study_logs.hours_logged + excluded.hours_logged),
                notes = COALESCE(NULLIF(excluded.notes, ''), study_logs.notes)
            """,
            (day, hours, notes),
        )


def get_current_streak(db_path=DB_PATH, today=None):
    """Count consecutive days with logged hours, ending today.

    If today has no entry yet, the streak still counts through yesterday.
    """
    today = today or date.today()
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT date FROM study_logs WHERE hours_logged > 0"
        ).fetchall()
    logged = {date.fromisoformat(row["date"]) for row in rows}

    day = today if today in logged else today - timedelta(days=1)
    streak = 0
    while day in logged:
        streak += 1
        day -= timedelta(days=1)
    return streak


def get_completed_count(db_path=DB_PATH):
    """Return the total number of completed modules."""
    with get_connection(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM completed_modules").fetchone()[0]


def get_progress_summary(db_path=DB_PATH):
    """Return the current streak and total completed modules."""
    return {
        "current_streak": get_current_streak(db_path),
        "completed_modules": get_completed_count(db_path),
    }


if __name__ == "__main__":
    init_db()
    print(get_progress_summary())