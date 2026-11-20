import json
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional
from ultron.ai.base_provider import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    """Native Ollama Chat & Tool Calling Provider for local-only execution."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "qwen3.5:2b-q4_K_M",
        fallback_model: str = "qwen3:1.7b",
        timeout_seconds: int = 120,
        temperature: float = 0.3,
        num_ctx: int = 4096,
        keep_alive: str = "5m"
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout_seconds
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive

    def is_available(self) -> bool:
        """Checks if local Ollama daemon is reachable on host."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "UltronAgent/2.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Lists locally downloaded Ollama models."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "UltronAgent/2.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name") for m in data.get("models", [])]
        except Exception:
            return []

    def get_effective_model(self) -> str:
        """Resolves whether configured model or fallback model is available."""
        available = self.list_models()
        if not available:
            return self.model

        # 1. Exact match
        if self.model in available:
            return self.model

        # 2. Prefix match (e.g. qwen3.5:2b matches qwen3.5:2b-q4_K_M)
        base_name = self.model.split(":")[0]
        for m in available:
            if m.startswith(base_name):
                return m

        # 3. Fallback model
        if self.fallback_model in available:
            return self.fallback_model

        for m in available:
            if m.startswith(self.fallback_model.split(":")[0]):
                return m

        return available[0]

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calls the Ollama /api/chat endpoint with native tool definitions."""
        if not self.is_available():
            return {
                "success": False,
                "error": f"Ollama daemon is offline at {self.host}. Please ensure Ollama is installed and running.",
                "model": self.model
            }

        target_model = self.get_effective_model()
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": chat_messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.temperature,
                "num_ctx": self.num_ctx
            },
            "keep_alive": self.keep_alive
        }

        if tools:
            payload["tools"] = tools

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "UltronAgent/2.0"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                message = data.get("message", {})
                return {
                    "success": True,
                    "message": message,
                    "model": target_model,
                    "done_reason": data.get("done_reason")
                }
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            return {
                "success": False,
                "error": f"Ollama HTTP {e.code}: {error_body or str(e)}",
                "model": target_model
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ollama inference error: {str(e)}",
                "model": target_model
            }
