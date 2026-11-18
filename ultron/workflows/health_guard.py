from typing import Dict, Any
from ultron.tools.system_monitor import SystemMonitor
from ultron.tools.notifier import Notifier
from ultron.persona import get_quote

class HealthGuardWorkflow:
    def __init__(self, monitor: SystemMonitor, notifier: Notifier):
        self.monitor = monitor
        self.notifier = notifier

    def run(self, cpu_thresh: float = 80.0, ram_thresh: float = 85.0, disk_thresh: float = 90.0) -> Dict[str, Any]:
        """Runs an autonomous health evaluation and responds to irregularities."""
        eval_result = self.monitor.evaluate_health(cpu_thresh, ram_thresh, disk_thresh)
        status = eval_result.get("status", "UNKNOWN")
        issues = eval_result.get("issues", [])

        if status == "OPTIMAL":
            self.notifier.log("INFO", "Autonomous health check completed: All systems nominal.")
        else:
            self.notifier.warning(f"Health anomaly detected [{status}]: {', '.join(issues)}")
            self.notifier.quote(get_quote("anomaly"))
            
            top_cpu = eval_result.get("metrics", {}).get("top_processes_by_cpu", [])
            top_mem = eval_result.get("metrics", {}).get("top_processes_by_memory", [])
            
            detail_msg = f"Top CPU: {top_cpu[0]['name'] if top_cpu else 'N/A'} | Top RAM: {top_mem[0]['name'] if top_mem else 'N/A'}"
            self.notifier.info(f"Anomaly telemetry: {detail_msg}")

            if status == "CRITICAL":
                self.notifier.toast("Ultron Alert: Critical Resource Load", f"{'; '.join(issues[:2])}")

        return eval_result
