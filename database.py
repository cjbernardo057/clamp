import os
import sqlite3

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    psycopg2 = None

DATABASE_URL = os.environ.get("DATABASE_URL")

class DBWrapper:
    def __init__(self, conn):
        self.conn = conn
        self.is_postgres = DATABASE_URL is not None

    def execute(self, query, params=()):
        if self.is_postgres:
            # PostgreSQL uses %s instead of ?
            query = query.replace("?", "%s")
            
            # Convert INSERT to use RETURNING id if needed
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor
        else:
            return self.conn.execute(query, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

def get_db():
    if DATABASE_URL:
        # Render PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
        return DBWrapper(conn)
    else:
        # Local SQLite connection
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pc_management.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return DBWrapper(conn)

def init_db():
    connection = get_db()
    
    # We need to use SERIAL instead of AUTOINCREMENT for PostgreSQL
    id_type = "SERIAL PRIMARY KEY" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"

    # =========================
    # COMPUTERS TABLE
    # =========================
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS computers (
            id {id_type},
            computer_name TEXT NOT NULL,
            comlab TEXT NOT NULL,
            status TEXT NOT NULL,
            processor TEXT,
            motherboard TEXT,
            ram TEXT,
            ram_slots INTEGER DEFAULT 1,
            storage TEXT,
            gpu TEXT,
            psu TEXT,
            cooling TEXT,
            computer_case TEXT,
            monitor TEXT,
            keyboard TEXT,
            mouse TEXT
        )
    """)

    # =========================
    # ISSUE REPORTS TABLE
    # =========================
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS issue_reports (
            id {id_type},
            reported_by TEXT NOT NULL,
            comlab TEXT NOT NULL,
            computer_name TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # ACCOUNTS TABLE
    # =========================
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS accounts (
            id {id_type},
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    # =========================
    # ISSUE RESOLUTIONS TABLE
    # =========================
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS issue_resolutions (
            id {id_type},
            report_id INTEGER NOT NULL,
            action_taken TEXT NOT NULL,
            status_changed_to TEXT,
            resolved_by TEXT,
            resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES issue_reports(id) ON DELETE CASCADE
        )
    """)
    
    # =========================
    # ACTIVITY LOGS TABLE
    # =========================
    connection.execute(f"""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id {id_type},
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            computer_name TEXT,
            comlab TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()