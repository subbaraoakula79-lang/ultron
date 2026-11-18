import os
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "ollama": {
        "host": "http://localhost:11434",
        "model": "llama3:latest",
        "timeout_seconds": 60,
        "temperature": 0.3
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
        "temp_clean_older_than_days": 2
    },
    "logging": {
        "log_file": "ultron.log",
        "log_level": "INFO",
        "desktop_notifications": True
    }
}

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.data = self._load()

    def _load(self) -> dict:
        if not self.config_path.exists():
            self._save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                for key, val in loaded.items():
                    if isinstance(val, dict) and key in merged:
                        merged[key].update(val)
                    else:
                        merged[key] = val
                return merged
        except Exception:
            return DEFAULT_CONFIG.copy()

    def _save(self, data: dict):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[!] Warning: Failed to save config: {e}")

    def get(self, key: str, default=None):
        keys = key.split(".")
        current = self.data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key: str, value):
        keys = key.split(".")
        current = self.data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self._save(self.data)
