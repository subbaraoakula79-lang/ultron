import subprocess
import time
from typing import Dict, Any, Optional

BLOCKED_PATTERNS = [
    "format c:", "rd /s /q c:\\windows", "del /f /s /q c:\\windows",
    "rm -rf /", "mkfs", ":(){ :|:& };:"
]

class CommandExecutor:
    def __init__(self, default_timeout: int = 120):
        self.default_timeout = default_timeout

    def run(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Runs a system command with safety checks and timeout."""
        cmd_lower = command.lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern in cmd_lower:
                return {
                    "success": False,
                    "error": f"Directive rejected: Disallowed hazardous pattern '{pattern}' detected.",
                    "exit_code": -1
                }

        start_time = time.time()
        actual_timeout = timeout or self.default_timeout

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd
            )
            stdout, stderr = process.communicate(timeout=actual_timeout)
            duration = round(time.time() - start_time, 2)

            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "duration_seconds": duration,
                "command": command
            }
        except subprocess.TimeoutExpired:
            process.kill()
            return {
                "success": False,
                "error": f"Command timed out after {actual_timeout} seconds",
                "exit_code": -99
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "exit_code": -1
            }
