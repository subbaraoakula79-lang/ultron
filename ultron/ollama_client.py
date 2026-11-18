import json
import urllib.request
import urllib.error
import re
from typing import List, Dict, Any, Optional

class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434", default_model: str = "llama3:latest", timeout: int = 60):
        self.host = host.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    def is_online(self) -> bool:
        """Checks if the local Ollama daemon is reachable."""
        try:
            req = urllib.request.Request(f"{self.host}/api/version", headers={"User-Agent": "UltronAgent/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            try:
                req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "UltronAgent/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    return resp.status == 200
            except Exception:
                return False

    def list_models(self) -> List[str]:
        """Lists models installed in the local Ollama library."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "UltronAgent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                return models
        except Exception:
            return []

    def get_preferred_model(self) -> str:
        """Returns the configured model, or first available model if default is missing."""
        available = self.list_models()
        if not available:
            return self.default_model
        if self.default_model in available:
            return self.default_model
        # Check without tags
        for m in available:
            if m.startswith(self.default_model.split(":")[0]):
                return m
        return available[0]

    def generate(self, prompt: str, system: Optional[str] = None, model: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
        """Generates a text completion from Ollama."""
        target_model = model or self.get_preferred_model()
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if system:
            payload["system"] = system

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "UltronAgent/1.0"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "model": target_model,
                    "raw": result
                }
        except urllib.error.URLError as e:
            return {
                "success": False,
                "error": f"Failed to communicate with Ollama at {self.host}: {e.reason}",
                "response": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Ollama generation failed: {str(e)}",
                "response": ""
            }

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3) -> Dict[str, Any]:
        """Sends a conversation history to Ollama's chat API."""
        target_model = model or self.get_preferred_model()
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "UltronAgent/1.0"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                msg = result.get("message", {}).get("content", "")
                return {
                    "success": True,
                    "response": msg,
                    "model": target_model,
                    "raw": result
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }

    @staticmethod
    def extract_json_action(text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON tool invocation payload from LLM markdown blocks or raw text."""
        # Check ```json ... ``` blocks first
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # Try to find raw { "action": ... }
        match = re.search(r"(\{[\s\S]*\"action\"[\s\S]*\})", text)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        return None
