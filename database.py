import sqlite3

DB_NAME = "dengue_guardian.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS patient_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                fever INTEGER NOT NULL CHECK (fever IN (0, 1)),
                body_pain INTEGER NOT NULL CHECK (body_pain IN (0, 1)),
                skin_rash INTEGER NOT NULL CHECK (skin_rash IN (0, 1))
            )
        """)
def save_symptoms(fever, body_pain, skin_rash):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO patient_records (fever, body_pain, skin_rash)
            VALUES (?, ?, ?)
            """,
            (fever, body_pain, skin_rash)
        )
        return cursor.lastrowid

if __name__ == "__main__":
    create_tables()
    print("Dengue Guardian database and tables are ready!")