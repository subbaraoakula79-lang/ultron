import time
from typing import Any, Dict, Optional
from ultron.agent.permission_manager import PermissionManager
from ultron.agent.tool_registry import ToolRegistry


class ToolExecutor:
    """Safely executes registered tools with permission enforcement and verification."""

    def __init__(self, registry: ToolRegistry, permission_manager: PermissionManager):
        self.registry = registry
        self.permissions = permission_manager

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        confirmation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validates arguments, checks permissions, and executes the tool handler."""
        # 1. Existence check
        tool_meta = self.registry.get_tool(tool_name)
        if not tool_meta:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' does not exist in registry.",
                "tool": tool_name
            }

        # 2. Argument validation
        val_res = self.registry.validate_arguments(tool_name, arguments)
        if not val_res.get("valid"):
            return {
                "success": False,
                "error": val_res.get("error"),
                "tool": tool_name
            }

        # 3. Permission check
        perm_res = self.permissions.check_permission(tool_name, arguments, confirmed_token=confirmation_token)
        if not perm_res.get("allowed"):
            return {
                "success": False,
                "blocked": True,
                "risk": perm_res.get("risk"),
                "confirmation_token": perm_res.get("confirmation_token"),
                "message": perm_res.get("confirmation_prompt"),
                "tool": tool_name
            }

        # 4. Handler invocation
        handler = tool_meta["handler"]
        start_time = time.time()
        try:
            result = handler(**arguments)
            duration = round(time.time() - start_time, 3)

            # Ensure result is a dict
            if not isinstance(result, dict):
                result = {"result": result}

            # Verification of success
            is_success = result.get("success", True)
            if "error" in result and not result.get("success", False):
                is_success = False

            return {
                "success": is_success,
                "observation": result,
                "tool": tool_name,
                "duration_seconds": duration
            }
        except TypeError as e:
            return {
                "success": False,
                "error": f"Tool parameter mismatch: {str(e)}",
                "tool": tool_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unhandled exception during tool execution: {str(e)}",
                "tool": tool_name
            }
