import pytest
from ultron.agent.permission_manager import PermissionManager, RiskLevel


def test_permission_risk_levels():
    pm = PermissionManager()
    assert pm.get_risk_level("system_status") == RiskLevel.LOW
    assert pm.get_risk_level("desktop_app") == RiskLevel.LOW
    assert pm.get_risk_level("organize_folder") == RiskLevel.MEDIUM
    assert pm.get_risk_level("delete_file") == RiskLevel.HIGH
    assert pm.get_risk_level("send_message") == RiskLevel.HIGH
    assert pm.get_risk_level("run_command") == RiskLevel.HIGH


def test_low_risk_auto_allowed():
    pm = PermissionManager()
    res = pm.check_permission("system_status", {})
    assert res["allowed"] is True
    assert res["risk"] == "low"


def test_high_risk_blocked_without_token():
    pm = PermissionManager()
    res = pm.check_permission("delete_file", {"path": "test.txt"})
    assert res["allowed"] is False
    assert res["risk"] == "high"
    assert "confirmation_token" in res
    token = res["confirmation_token"]

    # Now verify token confirms it
    confirm_res = pm.check_permission("delete_file", {"path": "test.txt"}, confirmed_token=token)
    assert confirm_res["allowed"] is True


def test_audit_log_redaction():
    pm = PermissionManager()
    pm.check_permission("send_message", {"recipient": "+12345", "password": "supersecretpassword"})
    trail = pm.get_audit_trail()
    assert len(trail) > 0
    last_entry = trail[-1]
    assert last_entry["args"]["password"] == "[REDACTED]"
