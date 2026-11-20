import time
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Standard classification mapping
TOOL_RISK_MAP = {
    # Low Risk (Autonomous)
    "system_status": RiskLevel.LOW,
    "search_web": RiskLevel.LOW,
    "phone_status": RiskLevel.LOW,
    "phone_screenshot": RiskLevel.LOW,
    "desktop_app": RiskLevel.LOW,
    "artemis_status": RiskLevel.LOW,
    "list_tasks": RiskLevel.LOW,
    "speak": RiskLevel.LOW,
    "read_file": RiskLevel.LOW,
    "find_large_files": RiskLevel.LOW,

    # Medium Risk (Audit Logged)
    "create_file": RiskLevel.MEDIUM,
    "move_file": RiskLevel.MEDIUM,
    "organize_folder": RiskLevel.MEDIUM,
    "clean_temp": RiskLevel.MEDIUM,
    "backup_folder": RiskLevel.MEDIUM,
    "schedule_task": RiskLevel.MEDIUM,
    "phone_app": RiskLevel.MEDIUM,
    "phone_search": RiskLevel.MEDIUM,

    # High Risk (Requires Explicit User Confirmation)
    "delete_file": RiskLevel.HIGH,
    "send_message": RiskLevel.HIGH,
    "book_tickets": RiskLevel.HIGH,
    "install_software": RiskLevel.HIGH,
    "run_command": RiskLevel.HIGH,
    "artemis_launch": RiskLevel.HIGH,
}


class PermissionManager:
    """Enforces 3-tier security classification and confirmation staging for agent actions."""

    def __init__(self):
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def get_risk_level(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> RiskLevel:
        """Determines the risk tier for a tool invocation."""
        level = TOOL_RISK_MAP.get(tool_name, RiskLevel.HIGH)

        # Dynamic parameter escalations
        if tool_name == "clean_temp" and args and args.get("older_than_days", 1) < 0.1:
            return RiskLevel.HIGH

        return level

    def check_permission(self, tool_name: str, args: Dict[str, Any], confirmed_token: Optional[str] = None) -> Dict[str, Any]:
        """Checks if a tool invocation can proceed or requires user approval."""
        risk = self.get_risk_level(tool_name, args)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Low risk: Always allowed
        if risk == RiskLevel.LOW:
            self._log_audit(tool_name, risk, "ALLOWED_AUTONOMOUS", args)
            return {"allowed": True, "risk": risk.value}

        # 2. Medium risk: Allowed with audit logging
        if risk == RiskLevel.MEDIUM:
            self._log_audit(tool_name, risk, "ALLOWED_AUDITED", args)
            return {"allowed": True, "risk": risk.value}

        # 3. High risk: Requires explicit confirmation
        if confirmed_token and confirmed_token in self.pending_confirmations:
            pending = self.pending_confirmations.pop(confirmed_token)
            if pending.get("tool") == tool_name:
                self._log_audit(tool_name, risk, "ALLOWED_USER_CONFIRMED", args)
                return {"allowed": True, "risk": risk.value}

        # Generate a confirmation token for staging
        token = f"CONFIRM-{tool_name}-{int(time.time() * 1000) % 100000}"
        self.pending_confirmations[token] = {
            "tool": tool_name,
            "args": args,
            "timestamp": timestamp,
            "created_at": time.time()
        }

        self._log_audit(tool_name, risk, "BLOCKED_REQUIRES_CONFIRMATION", args)
        return {
            "allowed": False,
            "risk": risk.value,
            "confirmation_token": token,
            "confirmation_prompt": (
                f"[HIGH-RISK ACTION REQUIRED]: Action '{tool_name}' requires your explicit authorization.\n"
                f"Parameters: {args}\n"
                f"To confirm, reply with: confirm {token}"
            )
        }

    def _log_audit(self, tool_name: str, risk: RiskLevel, decision: str, args: Dict[str, Any]):
        """Sanitizes arguments (redacting credentials/passwords) and records audit trail."""
        sanitized_args = {}
        for k, v in args.items():
            if any(secret in k.lower() for secret in ["password", "token", "key", "secret", "pin", "otp"]):
                sanitized_args[k] = "[REDACTED]"
            else:
                sanitized_args[k] = str(v)[:200]

        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tool": tool_name,
            "risk": risk.value,
            "decision": decision,
            "args": sanitized_args
        }
        self.audit_log.append(entry)
        # Keep memory footprint bounded
        if len(self.audit_log) > 200:
            self.audit_log.pop(0)

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        return list(self.audit_log)
