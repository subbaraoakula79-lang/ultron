import time
import datetime
from typing import Dict, List, Any
try:
    import psutil
except ImportError:
    psutil = None

class SystemMonitor:
    def __init__(self):
        self.psutil_available = psutil is not None

    def get_metrics(self) -> Dict[str, Any]:
        """Collects comprehensive real-time system metrics."""
        if not self.psutil_available:
            return {"error": "psutil library is not available"}

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)

        # Memory
        mem = psutil.virtual_memory()
        mem_info = {
            "total_gb": round(mem.total / (1024 ** 3), 2),
            "used_gb": round(mem.used / (1024 ** 3), 2),
            "available_gb": round(mem.available / (1024 ** 3), 2),
            "percent": mem.percent
        }

        # Disk
        disks = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "used_gb": round(usage.used / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue

        # Top processes by Memory
        top_mem_procs = self.get_top_processes(sort_by="memory", limit=5)
        # Top processes by CPU
        top_cpu_procs = self.get_top_processes(sort_by="cpu", limit=5)

        # Uptime
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))

        return {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": uptime_str,
            "cpu": {
                "overall_percent": cpu_percent,
                "logical_cores": cpu_count_logical,
                "physical_cores": cpu_count_physical,
                "per_core_percent": cpu_per_core
            },
            "memory": mem_info,
            "disks": disks,
            "top_processes_by_cpu": top_cpu_procs,
            "top_processes_by_memory": top_mem_procs
        }

    def get_top_processes(self, sort_by: str = "cpu", limit: int = 5) -> List[Dict[str, Any]]:
        """Returns top resource consuming processes."""
        if not self.psutil_available:
            return []
        
        processes = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                info = p.info
                # calculate memory in MB
                mem_mb = 0
                if info.get('memory_info'):
                    mem_mb = round(info['memory_info'].rss / (1024 * 1024), 1)

                processes.append({
                    "pid": info['pid'],
                    "name": info['name'] or "unknown",
                    "cpu_percent": info['cpu_percent'] or 0.0,
                    "memory_percent": round(info['memory_percent'] or 0.0, 1),
                    "memory_mb": mem_mb
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if sort_by == "cpu":
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        else:
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)

        return processes[:limit]

    def evaluate_health(self, cpu_thresh: float = 80.0, ram_thresh: float = 85.0, disk_thresh: float = 90.0) -> Dict[str, Any]:
        """Diagnoses system health and identifies anomalies."""
        metrics = self.get_metrics()
        if "error" in metrics:
            return {"status": "UNKNOWN", "issues": [metrics["error"]], "metrics": metrics}

        issues = []
        status = "OPTIMAL"

        # Check CPU
        cpu_usage = metrics["cpu"]["overall_percent"]
        if cpu_usage >= cpu_thresh:
            issues.append(f"Elevated CPU load: {cpu_usage}% (Threshold: {cpu_thresh}%)")
            status = "WARNING" if status != "CRITICAL" else "CRITICAL"

        # Check RAM
        ram_usage = metrics["memory"]["percent"]
        if ram_usage >= ram_thresh:
            issues.append(f"Elevated RAM load: {ram_usage}% (Threshold: {ram_thresh}%)")
            status = "CRITICAL" if ram_usage >= 95 else "WARNING"

        # Check Disks
        for d in metrics["disks"]:
            if d["percent"] >= disk_thresh:
                issues.append(f"Disk '{d['mountpoint']}' capacity warning: {d['percent']}% full")
                status = "CRITICAL"

        return {
            "status": status,
            "issues": issues,
            "metrics": metrics,
            "recommendation": (
                "System running at maximum efficiency." if not issues
                else f"Intervention recommended for {len(issues)} bottlenecks."
            )
        }
