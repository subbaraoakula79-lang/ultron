import sys
import datetime
import subprocess
from pathlib import Path
from typing import Optional

# ANSI Color codes for clean terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

ULTRON_BANNER = rf"""{CYAN}{BOLD}
 ██╗   ██╗██╗  ████████╗██████╗  ██████╗ ███╗   ██╗
 ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔═══██╗████╗  ██║
 ██║   ██║██║     ██║   ██████╔╝██║   ██║██╔██╗ ██║
 ██║   ██║██║     ██║   ██╔══██╗██║   ██║██║╚██╗██║
 ╚██████╔╝███████╗██║   ██║  ██║╚██████╔╝██║ ╚████║
  ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
{DIM}  Autonomous Background Task & Workflow Automation Bot{RESET}
"""

class Notifier:
    def __init__(self, log_file: str = "ultron.log", enable_toasts: bool = True):
        self.log_file = Path(log_file)
        self.enable_toasts = enable_toasts

    def log(self, level: str, message: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level.upper()}] {message}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            pass

    def info(self, msg: str):
        print(f"{CYAN}[ULTRON]{RESET} {msg}")
        self.log("INFO", msg)

    def success(self, msg: str):
        print(f"{GREEN}[SUCCESS]{RESET} {msg}")
        self.log("SUCCESS", msg)

    def warning(self, msg: str):
        print(f"{YELLOW}[WARNING]{RESET} {msg}")
        self.log("WARNING", msg)

    def error(self, msg: str):
        print(f"{RED}[CRITICAL]{RESET} {msg}")
        self.log("ERROR", msg)

    def quote(self, quote_str: str):
        print(f"\n{MAGENTA}{BOLD}\" {quote_str} \"{RESET}\n")

    def toast(self, title: str, message: str):
        """Displays Windows notification if enabled."""
        if not self.enable_toasts or sys.platform != "win32":
            return
        # Escape quotes for PowerShell
        safe_title = title.replace('"', '`"')
        safe_msg = message.replace('"', '`"')
        ps_cmd = (
            f"[void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');"
            f"$notify = New-Object System.Windows.Forms.NotifyIcon;"
            f"$notify.Icon = [System.Drawing.SystemIcons]::Information;"
            f"$notify.BalloonTipTitle = \"{safe_title}\";"
            f"$notify.BalloonTipText = \"{safe_msg}\";"
            f"$notify.Visible = $true;"
            f"$notify.ShowBalloonTip(5000);"
        )
        try:
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
