import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# Approved application allowlist mapping names to candidate system paths/executables
APP_ALLOWLIST: Dict[str, List[str]] = {
    "calc": [
        "calc.exe",
        r"C:\Windows\System32\calc.exe"
    ],
    "calculator": [
        "calc.exe",
        r"C:\Windows\System32\calc.exe"
    ],
    "notepad": [
        "notepad.exe",
        r"C:\Windows\System32\notepad.exe"
    ],
    "code": [
        str(Path(os.environ.get("LOCALAPPDATA", "")) / r"Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
        "code.cmd"
    ],
    "vscode": [
        str(Path(os.environ.get("LOCALAPPDATA", "")) / r"Programs\Microsoft VS Code\Code.exe"),
        r"C:\Program Files\Microsoft VS Code\Code.exe",
        "code.cmd"
    ],
    "chrome": [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path(os.environ.get("LOCALAPPDATA", "")) / r"Google\Chrome\Application\chrome.exe")
    ],
    "edge": [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ],
    "spotify": [
        str(Path(os.environ.get("APPDATA", "")) / r"Spotify\Spotify.exe")
    ]
}


class AppLauncher:
    """Safe, non-shell application launcher with verified executable paths."""

    def __init__(self):
        self.allowlist = APP_ALLOWLIST

    def list_supported_apps(self) -> List[str]:
        return list(self.allowlist.keys())

    def resolve_executable(self, app_name: str) -> Optional[str]:
        app_key = app_name.lower().strip()
        candidates = self.allowlist.get(app_key, [])
        for candidate in candidates:
            # Check absolute path
            p = Path(candidate)
            if p.is_file():
                return str(p)

            # Check in PATH
            found = self._which(candidate)
            if found:
                return found

        return None

    def _which(self, program: str) -> Optional[str]:
        from shutil import which
        return which(program)

    def launch(self, app_name: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        """Launches an approved application safely without shell=True."""
        exe = self.resolve_executable(app_name)
        if not exe:
            # Check if it's a known Windows system executable
            clean_name = app_name.lower().strip()
            if clean_name in ["calc", "notepad"]:
                exe = f"{clean_name}.exe"
            else:
                return {
                    "success": False,
                    "error": f"Application '{app_name}' is not in the approved allowlist or not installed on this system.",
                    "supported_apps": self.list_supported_apps()
                }

        cmd = [exe]
        if target_file and Path(target_file).exists():
            cmd.append(str(Path(target_file).resolve()))

        try:
            # Use subprocess without shell to prevent injection
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            )
            return {
                "success": True,
                "app": app_name,
                "executable": exe,
                "pid": proc.pid,
                "target_file": target_file
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to launch '{app_name}': {str(e)}"
            }
