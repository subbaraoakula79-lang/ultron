import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List, Optional
from ultron.ollama_client import OllamaClient

class BaseProvider:
    def is_available(self) -> bool:
        raise NotImplementedError

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

class GLMProvider(BaseProvider):
    """GLM / Zhipu AI BigModel Provider (glm-4-flash is a 100% free open-weights model)."""
    DEFAULT_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: str = "glm-4-flash", endpoint: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPU_API_KEY") or os.environ.get("OLLAMA_API_KEY")
        self.model = model
        self.endpoint = endpoint or os.environ.get("GLM_ENDPOINT") or self.DEFAULT_ENDPOINT

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "No GLM API key configured."}

        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": 0.3,
            "stream": False
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "UltronAgent/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "provider": f"GLM Open Model ({self.model})",
                    "model": self.model
                }
        except Exception as e:
            return {"success": False, "error": f"GLM API request error at {self.endpoint}: {str(e)}"}

class OllamaProvider(BaseProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3:latest"):
        self.client = OllamaClient(host=host, default_model=model)
        self.model = model

    def is_available(self) -> bool:
        return self.client.is_online()

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        msgs = list(messages)
        if system_prompt:
            msgs = [{"role": "system", "content": system_prompt}] + msgs
        res = self.client.chat(msgs, model=self.model)
        return {
            "success": res.get("success", False),
            "response": res.get("response", ""),
            "provider": "Ollama (Local)",
            "model": self.model,
            "error": res.get("error")
        }

class GitHubModelsProvider(BaseProvider):
    """Free LLM inference provided by GitHub Models using a GitHub Personal Access Token."""
    ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"

    def __init__(self, token: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.token)

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.token:
            return {"success": False, "error": "No GitHub Token configured (set GITHUB_TOKEN environment variable)."}

        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": 0.3
        }

        req = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "UltronAgent/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "provider": "GitHub Models (Free API)",
                    "model": self.model
                }
        except Exception as e:
            return {"success": False, "error": f"GitHub Models error: {str(e)}"}

class GroqProvider(BaseProvider):
    """Ultra-fast free tier LLM inference via Groq Cloud."""
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "No Groq API key (set GROQ_API_KEY)."}

        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": 0.3
        }

        req = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "UltronAgent/1.0"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "provider": "Groq Cloud (Free Tier)",
                    "model": self.model
                }
        except Exception as e:
            return {"success": False, "error": f"Groq API error: {str(e)}"}

class GeminiProvider(BaseProvider):
    """Google Gemini API developer free tier."""
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "No Gemini API key (set GEMINI_API_KEY)."}

        contents = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": 0.3}
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidate = data.get("candidates", [{}])[0]
                text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                return {
                    "success": True,
                    "response": text,
                    "provider": "Google Gemini (Free Tier)",
                    "model": self.model
                }
        except Exception as e:
            return {"success": False, "error": f"Gemini API error: {str(e)}"}

class OpenRouterProvider(BaseProvider):
    """OpenRouter free models (:free suffix)."""
    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-3.3-70b-instruct:free"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "No OpenRouter API key (set OPENROUTER_API_KEY)."}

        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        msgs.extend(messages)

        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": 0.3
        }

        req = urllib.request.Request(
            self.ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/ultron-agent",
                "X-Title": "Ultron Agent"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "provider": "OpenRouter (:free tier)",
                    "model": self.model
                }
        except Exception as e:
            return {"success": False, "error": f"OpenRouter error: {str(e)}"}

class ProviderManager:
    """Intelligently detects, ranks, and selects the active AI provider."""
    def __init__(self, config_data: Dict[str, Any]):
        self.config = config_data
        providers_cfg = config_data.get("providers", {})
        
        # Load tokens from config or env
        glm_key = providers_cfg.get("glm_api_key") or os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPU_API_KEY") or os.environ.get("OLLAMA_API_KEY")
        glm_model = providers_cfg.get("glm_model", "glm-4-flash")
        glm_endpoint = providers_cfg.get("glm_endpoint", "https://open.bigmodel.cn/api/paas/v4/chat/completions")

        gh_token = providers_cfg.get("github_token") or os.environ.get("GITHUB_TOKEN")
        groq_key = providers_cfg.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        gemini_key = providers_cfg.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        openrouter_key = providers_cfg.get("openrouter_api_key") or os.environ.get("OPENROUTER_API_KEY")

        ollama_cfg = config_data.get("ollama", {})
        self.providers: Dict[str, BaseProvider] = {
            "glm": GLMProvider(api_key=glm_key, model=glm_model, endpoint=glm_endpoint),
            "ollama": OllamaProvider(host=ollama_cfg.get("host", "http://localhost:11434"), model=ollama_cfg.get("model", "llama3:latest")),
            "github": GitHubModelsProvider(token=gh_token),
            "groq": GroqProvider(api_key=groq_key),
            "gemini": GeminiProvider(api_key=gemini_key),
            "openrouter": OpenRouterProvider(api_key=openrouter_key)
        }

    def get_active_provider(self) -> Optional[BaseProvider]:
        """Returns the first responsive/configured provider."""
        # 1. If GLM / Free Open-Source provider is configured, prioritize it
        if self.providers["glm"].is_available():
            return self.providers["glm"]

        # 2. Check local Ollama if online
        if self.providers["ollama"].is_available():
            return self.providers["ollama"]

        # 3. Check other free cloud API providers
        for name in ["groq", "github", "gemini", "openrouter"]:
            if self.providers[name].is_available():
                return self.providers[name]

        return None

    def get_status_report(self) -> List[Dict[str, Any]]:
        """Reports the health and readiness of all providers."""
        report = []
        for name, p in self.providers.items():
            avail = p.is_available()
            details = "Active and ready" if avail else "Missing API key / token"
            if name == "ollama" and not avail:
                details = "Ollama server not running on port 11434"
            elif name == "glm" and avail:
                details = f"Active ({getattr(p, 'model', 'glm-4-flash')} @ {getattr(p, 'endpoint', '')})"

            report.append({
                "provider": name,
                "status": "READY" if avail else "NOT_CONFIGURED" if name != "ollama" else "OFFLINE",
                "details": details
            })
        return report
