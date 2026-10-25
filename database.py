import sqlite3
import os


DATABASE = os.path.join(
    "/var/data", 
    "pc_management.db"
) if os.path.exists("/var/data") else os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "pc_management.db"
)

    
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():

    connection = get_db()

    # =========================
    # COMPUTERS TABLE
    # =========================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS computers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # Add missing columns if the database was created using
    # an older version of the system.

    computer_columns = connection.execute(
        "PRAGMA table_info(computers)"
    ).fetchall()

    computer_column_names = [
        column["name"] for column in computer_columns
    ]

    computer_new_columns = {
        "processor": "TEXT",
        "motherboard": "TEXT",
        "ram": "TEXT",
        "ram_slots": "INTEGER DEFAULT 1",
        "storage": "TEXT",
        "gpu": "TEXT",
        "psu": "TEXT",
        "cooling": "TEXT",
        "computer_case": "TEXT",
        "monitor": "TEXT",
        "keyboard": "TEXT",
        "mouse": "TEXT"
    }

    for column_name, column_type in computer_new_columns.items():

        if column_name not in computer_column_names:

            connection.execute(
                f"""
                ALTER TABLE computers
                ADD COLUMN {column_name} {column_type}
                """
            )

    # =========================
    # ISSUE REPORTS TABLE
    # =========================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS issue_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reported_by TEXT NOT NULL,
            comlab TEXT NOT NULL,
            computer_name TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # Add missing columns to old issue_reports table.

    report_columns = connection.execute(
        "PRAGMA table_info(issue_reports)"
    ).fetchall()

    report_column_names = [
        column["name"] for column in report_columns
    ]

    if "reported_by" not in report_column_names:

        connection.execute("""
            ALTER TABLE issue_reports
            ADD COLUMN reported_by TEXT DEFAULT ''
        """)

    if "comlab" not in report_column_names:

        connection.execute("""
            ALTER TABLE issue_reports
            ADD COLUMN comlab TEXT DEFAULT ''
        """)

    # If the database was created before created_at was
    # introduced, add it now (existing rows get NULL,
    # new rows get CURRENT_TIMESTAMP).

    if "created_at" not in report_column_names:

        connection.execute("""
            ALTER TABLE issue_reports
            ADD COLUMN created_at TIMESTAMP
        """)

    # =========================
    # ACCOUNTS TABLE
    # =========================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    connection.execute(""" 
        CREATE TABLE IF NOT EXISTS issue_resolutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            action_taken TEXT NOT NULL,
            status_changed_to TEXT,
            resolved_by TEXT,
            resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id)
                REFERENCES issue_reports(id)
                ON DELETE CASCADE
        )
    """)

        # =========================
    # ACTIVITY LOGS TABLE
    # =========================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            computer_name TEXT,
            comlab TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()