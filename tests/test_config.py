import os
import json
import pytest
from ultron.config import Config, DEFAULT_CONFIG


def test_default_config_loading(tmp_path):
    cfg_file = tmp_path / "test_config.json"
    config = Config(str(cfg_file))
    assert config.get("ai_provider") == "ollama"
    assert config.get("ollama.model") == "qwen3.5:2b-q4_K_M"
    assert config.get("ollama.num_ctx") == 4096
    assert config.get("automation.thresholds.cpu_percent_warning") == 80.0


def test_nested_deep_merge(tmp_path):
    cfg_file = tmp_path / "custom_config.json"
    custom_data = {
        "ollama": {
            "model": "custom-qwen:latest"
        },
        "automation": {
            "thresholds": {
                "cpu_percent_warning": 95.0
            }
        }
    }
    with open(cfg_file, "w") as f:
        json.dump(custom_data, f)

    config = Config(str(cfg_file))
    assert config.get("ollama.model") == "custom-qwen:latest"
    # Preserved un-overridden nested sibling keys:
    assert config.get("ollama.host") == "http://localhost:11434"
    assert config.get("automation.thresholds.cpu_percent_warning") == 95.0
    assert config.get("automation.thresholds.ram_percent_warning") == 85.0


def test_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:1.7b")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "2048")
    cfg_file = tmp_path / "env_config.json"
    config = Config(str(cfg_file))
    assert config.get("ollama.model") == "qwen3:1.7b"
    assert config.get("ollama.num_ctx") == 2048
