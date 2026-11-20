from typing import Any, Callable, Dict, List, Optional


class ToolRegistry:
    """Central registry for all Ultron tools with argument validation and schema generation."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable[..., Any]
    ):
        """Registers a tool with its JSON schema and execution handler."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_ollama_schemas(self) -> List[Dict[str, Any]]:
        """Converts registered tools into Ollama / OpenAI function calling schemas."""
        schemas = []
        for name, meta in self._tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["parameters"]
                }
            })
        return schemas

    def validate_arguments(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validates that required parameters are provided with expected types."""
        meta = self._tools.get(name)
        if not meta:
            return {"valid": False, "error": f"Tool '{name}' is not registered."}

        schema = meta.get("parameters", {})
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        # Check required fields
        for field in required:
            if field not in args:
                return {
                    "valid": False,
                    "error": f"Missing required parameter '{field}' for tool '{name}'."
                }

        # Type checking
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list
        }

        for arg_name, arg_val in args.items():
            if arg_name in properties:
                expected_type_str = properties[arg_name].get("type")
                if expected_type_str in type_mapping:
                    expected_python_type = type_mapping[expected_type_str]
                    if not isinstance(arg_val, expected_python_type):
                        return {
                            "valid": False,
                            "error": f"Parameter '{arg_name}' must be of type {expected_type_str}, got {type(arg_val).__name__}."
                        }

        return {"valid": True}
