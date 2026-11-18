import os
import subprocess
from pathlib import Path
from typing import Dict, Any

class ArtemisBridge:
    def __init__(self, artemis_dir: str = "artemis"):
        self.artemis_path = Path(artemis_dir).resolve()

    def is_installed(self) -> bool:
        return self.artemis_path.exists() and (self.artemis_path / "pyproject.toml").exists()

    def get_status(self) -> Dict[str, Any]:
        """Inspects Google ARTEMIS installation and Android device connectivity."""
        installed = self.is_installed()
        if not installed:
            return {
                "installed": False,
                "message": "Google ARTEMIS is not found in the workspace."
            }

        # Check ADB device status
        devices = []
        adb_found = False
        try:
            res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                adb_found = True
                lines = res.stdout.strip().split("\n")[1:]
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        devices.append({"id": parts[0], "status": parts[1] if len(parts) > 1 else "unknown"})
        except Exception:
            adb_found = False

        return {
            "installed": True,
            "path": str(self.artemis_path),
            "adb_available": adb_found,
            "connected_devices": devices,
            "launcher": str(self.artemis_path / "start.bat"),
            "readme": str(self.artemis_path / "README.md")
        }

    def launch_console(self) -> Dict[str, Any]:
        """Launches the Google ARTEMIS Mobile Automation web console."""
        bat_file = self.artemis_path / "start.bat"
        if not bat_file.exists():
            return {"success": False, "error": "artemis/start.bat not found."}

        try:
            # Start detached process on Windows
            subprocess.Popen(
                ["cmd.exe", "/c", str(bat_file)],
                cwd=str(self.artemis_path),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return {
                "success": True,
                "message": "Google ARTEMIS web console and agent environment initializing in new console window."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
