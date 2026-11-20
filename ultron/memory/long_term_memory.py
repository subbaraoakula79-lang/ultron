from typing import Any, Dict, List, Optional
from ultron.memory.database import MemoryDatabase


class LongTermMemory:
    """Stores user preferences, facts, and learned configurations across sessions."""

    def __init__(self, db: MemoryDatabase):
        self.db = db

    def store_fact(self, key: str, value: str, category: str = "preference", confidence: float = 1.0) -> bool:
        """Stores or updates a memory fact."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO long_term_memory (category, key, value, confidence, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                confidence=excluded.confidence,
                updated_at=CURRENT_TIMESTAMP;
            """, (category, key, value, confidence))
            conn.commit()
            return True

    def retrieve_fact(self, key: str) -> Optional[str]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM long_term_memory WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def list_all_facts(self) -> List[Dict[str, Any]]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category, key, value, confidence, updated_at FROM long_term_memory ORDER BY category, key")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def delete_fact(self, key: str) -> bool:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM long_term_memory WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
