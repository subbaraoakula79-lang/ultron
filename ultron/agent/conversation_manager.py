from typing import Any, Dict, List


class ConversationManager:
    """Maintains short-term conversational context bounded for 8 GB RAM efficiency."""

    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.history: List[Dict[str, Any]] = []

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})
        self._prune()

    def add_assistant_message(self, content: str, tool_calls: list = None):
        msg: Dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.history.append(msg)
        self._prune()

    def add_tool_message(self, content: str, tool_name: str = None):
        msg: Dict[str, Any] = {"role": "tool", "content": content}
        if tool_name:
            msg["name"] = tool_name
        self.history.append(msg)
        self._prune()

    def get_messages(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def clear(self):
        self.history.clear()

    def _prune(self):
        # Keep at most max_turns * 2 messages to prevent context overflow
        max_messages = self.max_turns * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
