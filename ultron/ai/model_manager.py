import os
import psutil
from typing import Any, Dict, List, Optional
from ultron.ai.base_provider import BaseAIProvider
from ultron.ai.ollama_provider import OllamaProvider


class ModelManager:
    """Orchestrates local model runtime selection, RAM safety checks, and provider health."""

    def __init__(self, config_data: Dict[str, Any]):
        self.config = config_data
        ollama_cfg = config_data.get("ollama", {})

        self.primary_provider = OllamaProvider(
            host=ollama_cfg.get("host", "http://localhost:11434"),
            model=ollama_cfg.get("model", "qwen3.5:2b-q4_K_M"),
            fallback_model=ollama_cfg.get("fallback_model", "qwen3:1.7b"),
            timeout_seconds=ollama_cfg.get("timeout_seconds", 120),
            temperature=ollama_cfg.get("temperature", 0.3),
            num_ctx=ollama_cfg.get("num_ctx", 4096),
            keep_alive=ollama_cfg.get("keep_alive", "5m")
        )

    def get_active_provider(self) -> BaseAIProvider:
        """Returns the primary local provider."""
        return self.primary_provider

    def check_ram_headroom(self) -> Dict[str, Any]:
        """Monitors system memory to prevent out-of-memory thrashing on 8 GB machines."""
        mem = psutil.virtual_memory()
        free_mb = round(mem.available / (1024 * 1024), 1)
        total_mb = round(mem.total / (1024 * 1024), 1)
        used_percent = mem.percent

        is_critical = free_mb < 600.0
        is_warning = free_mb < 1000.0

        recommended_model = self.primary_provider.model
        if is_warning:
            recommended_model = self.primary_provider.fallback_model

        return {
            "total_mb": total_mb,
            "free_mb": free_mb,
            "used_percent": used_percent,
            "is_warning": is_warning,
            "is_critical": is_critical,
            "recommended_model": recommended_model
        }

    def get_status_report(self) -> Dict[str, Any]:
        """Produces diagnostic status for HUD display."""
        is_online = self.primary_provider.is_available()
        models = self.primary_provider.list_models() if is_online else []
        effective_model = self.primary_provider.get_effective_model() if is_online else self.primary_provider.model
        ram_info = self.check_ram_headroom()

        return {
            "provider": "ollama",
            "online": is_online,
            "host": self.primary_provider.host,
            "configured_model": self.primary_provider.model,
            "effective_model": effective_model,
            "available_models": models,
            "ram_status": ram_info,
            "cloud_disabled": True
        }
