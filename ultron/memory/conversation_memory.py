import json
from typing import Any, Dict, List, Optional
from ultron.memory.database import MemoryDatabase

SENSITIVE_PATTERNS = ["password", "token", "api_key", "secret", "otp", "pin", "cvv"]


class ConversationMemory:
    """Stores and retrieves conversational turns with privacy redaction."""

    def __init__(self, db: MemoryDatabase):
        self.db = db

    def _sanitize(self, text: str) -> str:
        lower = text.lower()
        if any(pat in lower for pat in SENSITIVE_PATTERNS):
            # Redact common credential assignments if found
            import re
            return re.sub(r"(?i)(password|token|key|secret|otp)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
        return text

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        clean_content = self._sanitize(content)
        tc_json = json.dumps(tool_calls) if tool_calls else None

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (session_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
                (session_id, role, clean_content, tc_json)
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, tool_calls, timestamp FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = cursor.fetchall()

        results = []
        for r in reversed(rows):
            item = {
                "role": r["role"],
                "content": r["content"],
                "timestamp": r["timestamp"]
            }
            if r["tool_calls"]:
                try:
                    item["tool_calls"] = json.loads(r["tool_calls"])
                except Exception:
                    pass
            results.append(item)
        return results

    def clear_session(self, session_id: str) -> int:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount
