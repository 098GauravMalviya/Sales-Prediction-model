import os
import sqlite3


def get_db_path(db_filename: str = "market_analysis.db") -> str:
    """Return an absolute path to the SQLite database file."""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, db_filename)


def create_connection(db_path: str) -> sqlite3.Connection:
    """Create a SQLite connection to the specified database file."""

    conn = sqlite3.connect(db_path)
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Create the database schema for the market analysis dataset."""

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS market_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            product TEXT NOT NULL,
            price REAL NOT NULL,
            demand REAL NOT NULL,
            raw_material_price REAL NOT NULL,
            nvda_stock REAL NOT NULL,
            inflation REAL NOT NULL,
            pollution REAL NOT NULL,
            festival TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
        )
        """
    )

    conn.commit()


def main() -> None:
    """Create the database file, initialize the schema, and print table info."""

    db_path = get_db_path()
    conn = create_connection(db_path)

    create_schema(conn)

    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("Tables in database:")
    for table in tables:
        print(table[0])

    cursor.execute("PRAGMA table_info(market_data);")
    columns = cursor.fetchall()

    print("\nTable Structure:")
    for col in columns:
        print(col)

    conn.close()


if __name__ == "__main__":
    main()

