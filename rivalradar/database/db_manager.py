import sqlite3
from typing import Any


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS competitors (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                domain          TEXT NOT NULL,
                page_types      TEXT,
                market_segment  TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS portfolio_companies (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                name                TEXT NOT NULL,
                market_segment      TEXT,
                product_description TEXT,
                features_json       TEXT,
                pricing_context     TEXT,
                created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS raw_competitor_data (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id       INTEGER REFERENCES competitors(id),
                source_url          TEXT,
                page_type           TEXT,
                raw_text            TEXT,
                structured_summary  TEXT,
                embedding           BLOB,
                collected_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS product_gap_reports (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_company_id    INTEGER REFERENCES portfolio_companies(id),
                competitor_id           INTEGER REFERENCES competitors(id),
                gap_features            TEXT,
                strength_features       TEXT,
                integration_score       REAL,
                generated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pricing_predictions (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_id       INTEGER REFERENCES competitors(id),
                change_probability  REAL,
                predicted_timeline  TEXT,
                risk_level          TEXT,
                reasoning           TEXT,
                generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS action_recommendations (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_company_id    INTEGER REFERENCES portfolio_companies(id),
                competitor_id           INTEGER REFERENCES competitors(id),
                recommendation_type     TEXT,
                content                 TEXT,
                generated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # CRUD helpers                                                         #
    # ------------------------------------------------------------------ #

    def insert(self, table: str, data_dict: dict[str, Any]) -> int:
        columns = ", ".join(data_dict.keys())
        placeholders = ", ".join("?" * len(data_dict))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.conn.execute(sql, list(data_dict.values()))
        self.conn.commit()
        return cursor.lastrowid

    def fetch_all(self, table: str, filters_dict: dict[str, Any] | None = None) -> list[dict]:
        if filters_dict:
            where_clause = " AND ".join(f"{col} = ?" for col in filters_dict)
            sql = f"SELECT * FROM {table} WHERE {where_clause}"
            cursor = self.conn.execute(sql, list(filters_dict.values()))
        else:
            cursor = self.conn.execute(f"SELECT * FROM {table}")
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, table: str, filters_dict: dict[str, Any]) -> dict | None:
        where_clause = " AND ".join(f"{col} = ?" for col in filters_dict)
        sql = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"
        cursor = self.conn.execute(sql, list(filters_dict.values()))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update(self, table: str, data_dict: dict[str, Any], where_dict: dict[str, Any]):
        set_clause = ", ".join(f"{col} = ?" for col in data_dict)
        where_clause = " AND ".join(f"{col} = ?" for col in where_dict)
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        self.conn.execute(sql, list(data_dict.values()) + list(where_dict.values()))
        self.conn.commit()

    def execute_query(self, sql: str, params: tuple = ()) -> list[dict]:
        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
