import json
import sqlite3
from datetime import date, datetime, timedelta
import streamlit as st


@st.cache_resource
def get_conn(db_path: str = "progress.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS completed_modules (
            module_id TEXT PRIMARY KEY,
            completed_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS study_logs (
            log_date TEXT PRIMARY KEY,
            hours_logged REAL,
            notes TEXT
        )
        """
    )
    conn.commit()
    return conn


def get_completed_set(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT module_id FROM completed_modules").fetchall()
    return {r[0] for r in rows}


def toggle_module_status(conn: sqlite3.Connection, module_id: str, is_done: bool) -> None:
    if is_done:
        conn.execute(
            "INSERT OR REPLACE INTO completed_modules (module_id, completed_at) VALUES (?, ?)",
            (module_id, datetime.now().isoformat()),
        )
    else:
        conn.execute("DELETE FROM completed_modules WHERE module_id = ?", (module_id,))
    conn.commit()


def log_study_session(conn: sqlite3.Connection, log_dt: str, hours: float, notes: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO study_logs (log_date, hours_logged, notes) VALUES (?, ?, ?)",
        (log_dt, hours, notes.strip()),
    )
    conn.commit()


def get_streak_and_hours(conn: sqlite3.Connection):
    rows = conn.execute(
        "SELECT log_date, hours_logged, notes FROM study_logs WHERE hours_logged > 0 ORDER BY log_date DESC"
    ).fetchall()
    total_hours = sum(float(r[1]) for r in rows)
    logged_dates = {date.fromisoformat(r[0]) for r in rows}

    streak = 0
    cursor = date.today()
    if cursor not in logged_dates:
        cursor = cursor - timedelta(days=1)
    while cursor in logged_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak, round(total_hours, 1), rows


def export_progress_json(conn: sqlite3.Connection) -> str:
    completed = [
        {"module_id": r[0], "completed_at": r[1]}
        for r in conn.execute(
            "SELECT module_id, completed_at FROM completed_modules ORDER BY completed_at"
        ).fetchall()
    ]
    logs = [
        {"log_date": r[0], "hours_logged": r[1], "notes": r[2]}
        for r in conn.execute(
            "SELECT log_date, hours_logged, notes FROM study_logs ORDER BY log_date DESC"
        ).fetchall()
    ]
    return json.dumps({"completed_modules": completed, "study_logs": logs}, indent=2)


def import_progress_json(conn: sqlite3.Connection, raw_text: str) -> None:
    payload = json.loads(raw_text)
    if not isinstance(payload, dict):
        raise ValueError("Backup JSON must be an object.")

    for item in payload.get("completed_modules", []):
        if "module_id" in item:
            conn.execute(
                "INSERT OR REPLACE INTO completed_modules (module_id, completed_at) VALUES (?, ?)",
                (str(item["module_id"]), item.get("completed_at") or datetime.now().isoformat()),
            )

    for item in payload.get("study_logs", []):
        if "log_date" in item and "hours_logged" in item:
            conn.execute(
                "INSERT OR REPLACE INTO study_logs (log_date, hours_logged, notes) VALUES (?, ?, ?)",
                (str(item["log_date"]), float(item["hours_logged"]), str(item.get("notes") or "")),
            )

    conn.commit()