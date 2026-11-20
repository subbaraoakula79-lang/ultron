import os
import shutil
import psutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from ultron.tools.desktop.app_launcher import AppLauncher
from ultron.tools.desktop.screen_capture import ScreenCapture
from ultron.tools.desktop.window_manager import WindowManager


class DesktopController:
    """Consolidated desktop automation suite with strict permission checks and preview guards."""

    def __init__(self):
        self.launcher = AppLauncher()
        self.screen_capture = ScreenCapture()
        self.window_manager = WindowManager()

    def open_application(self, app_name: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        return self.launcher.launch(app_name, target_file=target_file)

    def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        return self.screen_capture.capture_screen(filename)

    def get_system_status(self) -> Dict[str, Any]:
        """Collects live CPU, RAM, disk, and load metrics."""
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.2)
        disk = psutil.disk_usage(os.path.abspath(os.sep))

        return {
            "success": True,
            "cpu_percent": cpu_pct,
            "ram_total_mb": round(vm.total / (1024 * 1024), 1),
            "ram_free_mb": round(vm.available / (1024 * 1024), 1),
            "ram_used_percent": vm.percent,
            "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 1),
            "disk_used_percent": disk.percent
        }

    def search_files(self, base_dir: str, pattern: str, max_results: int = 20) -> Dict[str, Any]:
        """Safely searches for files matching a glob pattern."""
        p = Path(base_dir).resolve()
        if not p.is_dir():
            return {"success": False, "error": f"Directory not found: {base_dir}"}

        matches = []
        try:
            for item in p.glob(f"*{pattern}*"):
                if item.is_file():
                    matches.append({
                        "name": item.name,
                        "path": str(item),
                        "size_bytes": item.stat().st_size
                    })
                    if len(matches) >= max_results:
                        break
            return {"success": True, "count": len(matches), "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_text_file(self, file_path: str, max_lines: int = 50) -> Dict[str, Any]:
        """Safely reads lines from a text file."""
        p = Path(file_path).resolve()
        if not p.is_file():
            return {"success": False, "error": f"File does not exist: {file_path}"}

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = [next(f) for _ in range(max_lines)]
            return {
                "success": True,
                "file": str(p),
                "lines_read": len(lines),
                "content": "".join(lines)
            }
        except StopIteration:
            return {"success": True, "file": str(p), "lines_read": len(lines), "content": "".join(lines)}
        except Exception as e:
            return {"success": False, "error": f"Could not read file: {str(e)}"}

    def preview_organize_downloads(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """Produces a safe preview of where files would be categorized without moving anything."""
        target_dir = Path(directory) if directory else Path.home() / "Downloads"
        if not target_dir.is_dir():
            return {"success": False, "error": f"Downloads directory '{target_dir}' not found."}

        categories = {
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv"],
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
            "Videos": [".mp4", ".mkv", ".mov", ".avi"],
            "Archives": [".zip", ".tar", ".gz", ".7z", ".rar"],
            "Executables": [".exe", ".msi", ".apk"]
        }

        preview = []
        for file in target_dir.iterdir():
            if file.is_file():
                ext = file.suffix.lower()
                target_folder = "Others"
                for cat, exts in categories.items():
                    if ext in exts:
                        target_folder = cat
                        break
                preview.append({
                    "file": file.name,
                    "target_folder": target_folder,
                    "size_bytes": file.stat().st_size
                })

        return {
            "success": True,
            "directory": str(target_dir),
            "files_to_organize": len(preview),
            "preview": preview[:50]
        }
