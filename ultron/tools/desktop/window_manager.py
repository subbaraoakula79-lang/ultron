import subprocess
from typing import Any, Dict, List


class WindowManager:
    """Manages and queries top-level Windows desktop application windows."""

    def list_open_windows(self) -> List[Dict[str, Any]]:
        """Lists active top-level windows that have visible titles."""
        ps_cmd = (
            "Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | "
            "Select-Object Id, ProcessName, MainWindowTitle | ConvertTo-Json -Compress"
        )
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=8
            )
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                return data
            return []
        except Exception:
            return []

    def is_app_running(self, app_name: str) -> bool:
        """Checks if any process matching app_name is currently active."""
        clean = app_name.lower()
        windows = self.list_open_windows()
        for w in windows:
            p_name = str(w.get("ProcessName", "")).lower()
            title = str(w.get("MainWindowTitle", "")).lower()
            if clean in p_name or clean in title:
                return True
        return False
