from typing import Any, Dict, List, Optional
from ultron.memory.database import MemoryDatabase
from ultron.memory.conversation_memory import ConversationMemory
from ultron.memory.long_term_memory import LongTermMemory


class MemoryManager:
    """Consolidated controller for conversation history and long-term facts."""

    def __init__(self, db_path: str = "ultron_memory.db"):
        self.db = MemoryDatabase(db_path)
        self.conversations = ConversationMemory(self.db)
        self.long_term = LongTermMemory(self.db)

    def record_turn(self, session_id: str, user_text: str, assistant_text: str, tool_calls: Optional[list] = None):
        self.conversations.save_message(session_id, "user", user_text)
        self.conversations.save_message(session_id, "assistant", assistant_text, tool_calls=tool_calls)

    def get_memory_context_prompt(self) -> str:
        """Assembles stored user facts and preferences to inject into agent context."""
        facts = self.long_term.list_all_facts()
        if not facts:
            return ""

        lines = ["[Persisted User Preferences & Memory]:"]
        for f in facts:
            lines.append(f"- {f['key']}: {f['value']}")
        return "\n".join(lines)
