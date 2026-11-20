import os
import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "ai_provider": "ollama",
    "ollama": {
        "host": "http://localhost:11434",
        "model": "qwen3.5:2b-q4_K_M",
        "fallback_model": "qwen3:1.7b",
        "timeout_seconds": 120,
        "temperature": 0.3,
        "num_ctx": 4096,
        "keep_alive": "5m"
    },
    "automation": {
        "daemon_tick_interval_seconds": 5,
        "health_check_interval_seconds": 300,
        "auto_cleanup_temp_interval_seconds": 3600 * 6,
        "thresholds": {
            "cpu_percent_warning": 80.0,
            "ram_percent_warning": 85.0,
            "disk_percent_warning": 90.0
        },
        "watch_paths": [
            str(Path.home() / "Downloads")
        ],
        "auto_organize_downloads": False,
        "temp_clean_older_than_days": 2,
        "schedules_file": "schedules.json"
    },
    "logging": {
        "log_file": "ultron.log",
        "log_level": "INFO",
        "desktop_notifications": True
    },
    "features": {
        "enable_voice": True,
        "enable_memory": True,
        "enable_android": True,
        "enable_desktop": True,
        "enable_web_search": True,
        "default_language": "auto"
    }
}


def _deep_merge(source: dict, destination: dict) -> dict:
    """Recursively merges source into destination."""
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            destination[key] = _deep_merge(value, destination[key].copy())
        else:
            destination[key] = value
    return destination


class Config:
    """Central configuration management with JSON persistence, deep merge, and ENV overrides."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        merged = json.loads(json.dumps(DEFAULT_CONFIG))

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    merged = _deep_merge(file_data, merged)
            except Exception:
                pass

        # Apply environment variable overrides
        if "AI_PROVIDER" in os.environ:
            merged["ai_provider"] = os.environ["AI_PROVIDER"]
        if "OLLAMA_HOST" in os.environ:
            merged["ollama"]["host"] = os.environ["OLLAMA_HOST"]
        if "OLLAMA_MODEL" in os.environ:
            merged["ollama"]["model"] = os.environ["OLLAMA_MODEL"]
        if "OLLAMA_FALLBACK_MODEL" in os.environ:
            merged["ollama"]["fallback_model"] = os.environ["OLLAMA_FALLBACK_MODEL"]
        if "OLLAMA_TIMEOUT" in os.environ:
            try:
                merged["ollama"]["timeout_seconds"] = int(os.environ["OLLAMA_TIMEOUT"])
            except ValueError:
                pass
        if "OLLAMA_TEMPERATURE" in os.environ:
            try:
                merged["ollama"]["temperature"] = float(os.environ["OLLAMA_TEMPERATURE"])
            except ValueError:
                pass
        if "OLLAMA_NUM_CTX" in os.environ:
            try:
                merged["ollama"]["num_ctx"] = int(os.environ["OLLAMA_NUM_CTX"])
            except ValueError:
                pass
        if "OLLAMA_KEEP_ALIVE" in os.environ:
            merged["ollama"]["keep_alive"] = os.environ["OLLAMA_KEEP_ALIVE"]

        return merged

    def get(self, key_path: str, default: Any = None) -> Any:
        """Retrieves a nested value using dot notation (e.g., 'automation.thresholds.cpu_percent_warning')."""
        keys = key_path.split(".")
        current = self.data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key_path: str, value: Any):
        """Sets a nested value using dot notation and saves to file."""
        keys = key_path.split(".")
        current = self.data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self.save()

    def save(self):
        """Persists current configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception:
            pass
