"""
SQLite persistence utilities shared across agents
"""
import sqlite3
import os
import logging
from contextlib import contextmanager
from . import config

logger = logging.getLogger(__name__)


def get_db_path() -> str:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    return config.DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they don't exist"""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id     TEXT PRIMARY KEY,
                full_name       TEXT NOT NULL,
                email           TEXT UNIQUE NOT NULL,
                phone           TEXT,
                buyer_type      TEXT NOT NULL,
                budget_min      REAL NOT NULL,
                budget_max      REAL NOT NULL,
                preferred_locations TEXT,
                created_at      TEXT DEFAULT (datetime('now')),
                raw_json        TEXT
            );

            CREATE TABLE IF NOT EXISTS properties (
                property_id     TEXT PRIMARY KEY,
                title           TEXT NOT NULL,
                location        TEXT NOT NULL,
                property_type   TEXT NOT NULL,
                price           REAL NOT NULL,
                area_sqft       REAL,
                bedrooms        INTEGER,
                bathrooms       INTEGER,
                amenities       TEXT,
                owner_name      TEXT,
                owner_contact   TEXT,
                status          TEXT DEFAULT 'active',
                created_at      TEXT DEFAULT (datetime('now')),
                raw_json        TEXT
            );

            CREATE TABLE IF NOT EXISTS market_insights (
                insight_id      TEXT PRIMARY KEY,
                property_id     TEXT NOT NULL,
                insight_type    TEXT NOT NULL,
                content         TEXT NOT NULL,
                embedded        INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(property_id) REFERENCES properties(property_id)
            );

            CREATE TABLE IF NOT EXISTS agent_logs (
                log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name      TEXT NOT NULL,
                event_type      TEXT NOT NULL,
                payload         TEXT,
                status          TEXT NOT NULL,
                created_at      TEXT DEFAULT (datetime('now'))
            );
        """)
    logger.info("Database initialized at %s", get_db_path())
