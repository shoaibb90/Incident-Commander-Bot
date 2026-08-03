import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import DB_PATH


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                category TEXT,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'new',
                reporter_id INTEGER,
                assigned_to INTEGER,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS incident_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id INTEGER,
                author_id INTEGER,
                note TEXT,
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id INTEGER,
                action TEXT,
                details TEXT,
                created_at TEXT
            )
        """)
        conn.commit()


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def now():
    return datetime.utcnow().isoformat(timespec="seconds")


# ---------- Users ----------

def get_user(telegram_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return dict(row) if row else None


def create_user(telegram_id, username, full_name):
    with get_conn() as conn:
        c = conn.cursor()
        count = c.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        # First-ever user is auto-promoted to admin (bootstrap step)
        role = "admin" if count == 0 else "pending"
        c.execute(
            "INSERT INTO users (telegram_id, username, full_name, role, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (telegram_id, username, full_name, role, now()),
        )
        conn.commit()
        return role


def set_role(telegram_id, role):
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?", (role, telegram_id)
        )
        conn.commit()


def list_users(role_filter=None):
    with get_conn() as conn:
        if role_filter:
            rows = conn.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY created_at", (role_filter,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at").fetchall()
        return [dict(r) for r in rows]


def get_user_by_id(user_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


# ---------- Incidents ----------

def create_incident(title, description, category, severity, reporter_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO incidents (title, description, category, severity, status, "
            "reporter_id, created_at, updated_at) VALUES (?, ?, ?, ?, 'new', ?, ?, ?)",
            (title, description, category, severity, reporter_id, now(), now()),
        )
        conn.commit()
        return c.lastrowid


def get_incident(incident_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)
        ).fetchone()
        return dict(row) if row else None


def list_incidents(status=None):
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM incidents WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM incidents ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def update_incident_status(incident_id, status):
    with get_conn() as conn:
        conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (status, now(), incident_id),
        )
        conn.commit()


def assign_incident(incident_id, assignee_user_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE incidents SET assigned_to = ?, updated_at = ? WHERE id = ?",
            (assignee_user_id, now(), incident_id),
        )
        conn.commit()


def delete_incident(incident_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM incidents WHERE id = ?", (incident_id,))
        conn.execute("DELETE FROM incident_notes WHERE incident_id = ?", (incident_id,))
        conn.commit()


def add_note(incident_id, author_id, note):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO incident_notes (incident_id, author_id, note, created_at) "
            "VALUES (?, ?, ?, ?)",
            (incident_id, author_id, note, now()),
        )
        conn.execute(
            "UPDATE incidents SET updated_at = ? WHERE id = ?", (now(), incident_id)
        )
        conn.commit()


def get_notes(incident_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM incident_notes WHERE incident_id = ? ORDER BY created_at",
            (incident_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats():
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM incidents").fetchone()["n"]
        by_status = conn.execute(
            "SELECT status, COUNT(*) AS n FROM incidents GROUP BY status"
        ).fetchall()
        by_severity = conn.execute(
            "SELECT severity, COUNT(*) AS n FROM incidents GROUP BY severity"
        ).fetchall()
        return {
            "total": total,
            "by_status": {r["status"]: r["n"] for r in by_status},
            "by_severity": {r["severity"]: r["n"] for r in by_severity},
        }


# ---------- Audit log ----------

def log_action(actor_id, action, details=""):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (actor_id, action, details, created_at) "
            "VALUES (?, ?, ?, ?)",
            (actor_id, action, details, now()),
        )
        conn.commit()


def get_audit_log(limit=20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
