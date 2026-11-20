import pytest
from ultron.memory.database import MemoryDatabase
from ultron.memory.conversation_memory import ConversationMemory
from ultron.memory.long_term_memory import LongTermMemory
from ultron.memory.memory_manager import MemoryManager


def test_conversation_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    db = MemoryDatabase(str(db_file))
    conv = ConversationMemory(db)

    # Save turn
    conv.save_message("sess_1", "user", "Hello Ultron")
    conv.save_message("sess_1", "assistant", "Greetings. Systems operational.")

    history = conv.get_recent_history("sess_1", limit=5)
    assert len(history) == 2
    assert history[0]["content"] == "Hello Ultron"
    assert history[1]["content"] == "Greetings. Systems operational."


def test_sensitive_credential_redaction(tmp_path):
    db_file = tmp_path / "test_redact.db"
    db = MemoryDatabase(str(db_file))
    conv = ConversationMemory(db)

    conv.save_message("sess_2", "user", "My password: secret12345")
    history = conv.get_recent_history("sess_2", limit=1)
    assert "secret12345" not in history[0]["content"]
    assert "[REDACTED]" in history[0]["content"]


def test_long_term_memory_facts(tmp_path):
    db_file = tmp_path / "test_ltm.db"
    mgr = MemoryManager(str(db_file))

    mgr.long_term.store_fact("user_name", "Subbarao", category="identity")
    mgr.long_term.store_fact("preferred_browser", "Chrome", category="preference")

    assert mgr.long_term.retrieve_fact("user_name") == "Subbarao"
    assert mgr.long_term.retrieve_fact("preferred_browser") == "Chrome"

    # Context assembly
    ctx = mgr.get_memory_context_prompt()
    assert "user_name: Subbarao" in ctx
    assert "preferred_browser: Chrome" in ctx

    # Deletion
    assert mgr.long_term.delete_fact("preferred_browser") is True
    assert mgr.long_term.retrieve_fact("preferred_browser") is None
