import json
from unittest.mock import MagicMock
import pytest
from ultron.hud_server import build_ultron_system, UltronHudHandler


def test_build_ultron_system():
    sys = build_ultron_system()
    assert sys["agent"] is not None
    assert sys["desktop"] is not None
    assert sys["model_mgr"] is not None
    assert sys["permission_mgr"] is not None
    assert "desktop_app" in sys["registry"].list_tools()
    assert "system_status" in sys["registry"].list_tools()


def test_hud_cors_origin_policy():
    handler = UltronHudHandler.__new__(UltronHudHandler)
    handler.headers = {"Origin": "http://localhost:8080"}
    assert handler._is_origin_allowed() is True

    handler.headers = {"Origin": "http://127.0.0.1:8080"}
    assert handler._is_origin_allowed() is True

    handler.headers = {"Origin": "http://malicious-external-site.com"}
    assert handler._is_origin_allowed() is False
