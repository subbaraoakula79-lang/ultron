from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIProvider(ABC):
    """Abstract base class for Ultron AI Model Providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the local runtime is online and responsive."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Lists available installed models."""
        pass

    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Sends chat messages and optional tool definitions to the provider.

        Returns a dictionary:
        {
            "success": bool,
            "message": {"role": "assistant", "content": str, "tool_calls": [...]},
            "model": str,
            "error": Optional[str]
        }
        """
        pass
