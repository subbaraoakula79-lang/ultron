import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryDatabase:
    """Manages the local SQLite persistence store for Ultron."""

    def __init__(self, db_path: str = "ultron_memory.db"):
        self.db_path = Path(db_path).resolve()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency and resilience
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Conversations table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Long-term preferences / memory facts table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mem_key ON long_term_memory(key);")
            conn.commit()
