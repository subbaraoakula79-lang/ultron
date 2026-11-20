import json
from unittest.mock import MagicMock, patch
import pytest
from ultron.ai.ollama_provider import OllamaProvider
from ultron.ai.model_manager import ModelManager


def test_ollama_provider_init():
    provider = OllamaProvider(
        host="http://localhost:11434",
        model="qwen3.5:2b-q4_K_M",
        fallback_model="qwen3:1.7b",
        num_ctx=4096,
        keep_alive="5m"
    )
    assert provider.model == "qwen3.5:2b-q4_K_M"
    assert provider.fallback_model == "qwen3:1.7b"
    assert provider.num_ctx == 4096
    assert provider.keep_alive == "5m"


def test_ollama_offline_handling():
    provider = OllamaProvider(host="http://127.0.0.1:9999", timeout_seconds=1)
    assert provider.is_available() is False
    res = provider.chat([{"role": "user", "content": "Hello"}])
    assert res["success"] is False
    assert "offline" in res["error"].lower()


def test_model_manager_ram_check():
    manager = ModelManager({"ollama": {"model": "qwen3.5:2b-q4_K_M"}})
    ram = manager.check_ram_headroom()
    assert "free_mb" in ram
    assert "total_mb" in ram
    assert "used_percent" in ram
    assert ram["total_mb"] > 0


def test_model_manager_status():
    manager = ModelManager({"ollama": {"model": "qwen3.5:2b-q4_K_M"}})
    status = manager.get_status_report()
    assert status["provider"] == "ollama"
    assert status["cloud_disabled"] is True
    assert status["configured_model"] == "qwen3.5:2b-q4_K_M"


def test_mocked_ollama_native_tool_call():
    provider = OllamaProvider()

    # Mock is_available, list_models, and direct chat call
    with patch.object(provider, "is_available", return_value=True), \
         patch.object(provider, "get_effective_model", return_value="qwen3.5:2b-q4_K_M"), \
         patch("urllib.request.urlopen") as mock_urlopen:

        mock_resp = MagicMock()
        mock_resp.status = 200
        chat_payload = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "desktop_app",
                            "arguments": {"app": "notepad"}
                        }
                    }
                ]
            },
            "done_reason": "stop"
        }
        mock_resp.read.return_value = json.dumps(chat_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "desktop_app",
                    "description": "Opens an application",
                    "parameters": {"type": "object", "properties": {"app": {"type": "string"}}}
                }
            }
        ]
        res = provider.chat([{"role": "user", "content": "open notepad"}], tools=tools)
        assert res["success"] is True
        assert "tool_calls" in res["message"]
        assert res["message"]["tool_calls"][0]["function"]["name"] == "desktop_app"
