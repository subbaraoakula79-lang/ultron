import json
from unittest.mock import MagicMock
import pytest
from ultron.agent.permission_manager import PermissionManager
from ultron.agent.tool_registry import ToolRegistry
from ultron.agent.tool_executor import ToolExecutor
from ultron.agent.planner import TaskPlanner
from ultron.agent.agent import UltronAgent
from ultron.ai.model_manager import ModelManager


def test_tool_registry_and_validation():
    registry = ToolRegistry()

    def dummy_app(app: str):
        return {"launched": app, "success": True}

    registry.register_tool(
        name="desktop_app",
        description="Launch an application",
        parameters={
            "type": "object",
            "properties": {"app": {"type": "string"}},
            "required": ["app"]
        },
        handler=dummy_app
    )

    assert "desktop_app" in registry.list_tools()

    # Valid arguments
    assert registry.validate_arguments("desktop_app", {"app": "notepad"})["valid"] is True

    # Missing required argument
    assert registry.validate_arguments("desktop_app", {})["valid"] is False

    # Schema output
    schemas = registry.get_ollama_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "desktop_app"


def test_planner_intent_matching():
    planner = TaskPlanner()
    plan_en = planner.plan_steps("open vscode")
    assert len(plan_en) == 1
    assert plan_en[0]["tool"] == "desktop_app"
    assert plan_en[0]["args"]["app"] == "code"

    plan_te = planner.plan_steps("సిస్టమ్ స్టేటస్ చెక్")
    assert len(plan_te) == 1
    assert plan_te[0]["tool"] == "system_status"


def test_agent_end_to_end_mocked():
    model_mgr = ModelManager({"ollama": {}})
    registry = ToolRegistry()
    permissions = PermissionManager()

    called_apps = []

    def dummy_open(app: str):
        called_apps.append(app)
        return {"opened": app, "success": True}

    registry.register_tool(
        name="desktop_app",
        description="Launch app",
        parameters={"type": "object", "properties": {"app": {"type": "string"}}, "required": ["app"]},
        handler=dummy_open
    )

    agent = UltronAgent(model_mgr, registry, permissions)

    # Test fallback path when Ollama offline
    res = agent.process("open vscode")
    assert "code" in called_apps
    assert "Execution Verified" in res or "Directive executed" in res
