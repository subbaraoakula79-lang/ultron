import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict


class ScreenCapture:
    """Takes screenshots of the Windows desktop using built-in .NET graphics without extra packages."""

    def __init__(self, output_dir: str = "screenshots"):
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_screen(self, filename: str = None) -> Dict[str, Any]:
        if not filename:
            filename = f"desktop_screenshot_{int(time.time())}.png"
        save_path = self.output_dir / filename

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('{str(save_path).replace("\\", "\\\\")}', [System.Drawing.Imaging.ImageFormat]::Png)
$gfx.Dispose()
$bmp.Dispose()
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=15
            )
            if save_path.exists() and save_path.stat().st_size > 0:
                return {
                    "success": True,
                    "file_path": str(save_path),
                    "file_size_bytes": save_path.stat().st_size
                }
            return {
                "success": False,
                "error": f"Screenshot command completed but file was not created: {res.stderr}"
            }
        except Exception as e:
            return {"success": False, "error": f"Screenshot capture error: {str(e)}"}
