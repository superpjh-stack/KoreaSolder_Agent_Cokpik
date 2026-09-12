"""Copy the local demo SQLite rows into an initialized PostgreSQL Data Hub."""
import os
import sqlite3
from pathlib import Path

from goryeo_solder_agent.data_hub import TABLES, PostgresRepository


def main():
    sqlite_path = Path(os.getenv("SQLITE_PATH", "goryeo_solder_demo.db"))
    url = os.environ["DATABASE_URL"]
    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    target = PostgresRepository(url)
    with target._connect() as connection:
        for table in TABLES:
            if table == "settings":
                continue
            rows = source.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                continue
            columns = [description[1] for description in source.execute(f"PRAGMA table_info({table})").fetchall()]
            placeholders = ",".join("?" for _ in columns)
            for row in rows:
                connection.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING", tuple(row))
    print(f"migrated {sqlite_path} to PostgreSQL")


if __name__ == "__main__":
    main()
