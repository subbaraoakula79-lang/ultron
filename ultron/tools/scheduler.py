import json
import time
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class TaskScheduler:
    def __init__(self, schedule_file: str = "schedules.json"):
        self.schedule_file = Path(schedule_file)
        self.jobs = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.schedule_file.exists():
            default_jobs = [
                {
                    "id": "job-sys-health",
                    "name": "Periodic System Health Check",
                    "action": "health_check",
                    "args": {"cpu_thresh": 80.0, "ram_thresh": 85.0},
                    "trigger_type": "interval",
                    "interval_seconds": 300,
                    "enabled": True,
                    "last_run": None,
                    "next_run": time.time() + 60,
                    "run_count": 0
                },
                {
                    "id": "job-temp-clean",
                    "name": "Daily Temp Cache Cleanup",
                    "action": "clean_temp",
                    "args": {"older_than_days": 1.0},
                    "trigger_type": "interval",
                    "interval_seconds": 86400,
                    "enabled": True,
                    "last_run": None,
                    "next_run": time.time() + 3600,
                    "run_count": 0
                }
            ]
            self._save(default_jobs)
            return default_jobs

        try:
            with open(self.schedule_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, jobs: List[Dict[str, Any]]):
        try:
            with open(self.schedule_file, "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=4)
        except Exception as e:
            print(f"[!] Warning: Failed to save schedules: {e}")

    def add_job(self, name: str, action: str, trigger_type: str = "interval",
                interval_seconds: int = 3600, daily_time: Optional[str] = None,
                args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Registers a new scheduled automation job."""
        job_id = f"job-{uuid.uuid4().hex[:6]}"
        now = time.time()

        if trigger_type == "daily" and daily_time:
            # calculate next occurrence of HH:MM
            target_h, target_m = map(int, daily_time.split(":"))
            today = datetime.datetime.now()
            target_dt = today.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
            if target_dt.timestamp() <= now:
                target_dt += datetime.timedelta(days=1)
            next_run = target_dt.timestamp()
        else:
            trigger_type = "interval"
            next_run = now + interval_seconds

        job = {
            "id": job_id,
            "name": name,
            "action": action,
            "args": args or {},
            "trigger_type": trigger_type,
            "interval_seconds": interval_seconds,
            "daily_time": daily_time,
            "enabled": True,
            "last_run": None,
            "next_run": next_run,
            "run_count": 0
        }

        self.jobs.append(job)
        self._save(self.jobs)
        return job

    def remove_job(self, job_id: str) -> bool:
        """Removes a job by ID."""
        initial_len = len(self.jobs)
        self.jobs = [j for j in self.jobs if j["id"] != job_id]
        if len(self.jobs) < initial_len:
            self._save(self.jobs)
            return True
        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """Returns all scheduled jobs with human-readable next run times."""
        result = []
        now = time.time()
        for j in self.jobs:
            item = j.copy()
            next_ts = item.get("next_run", 0)
            diff = int(next_ts - now)
            if diff <= 0:
                item["status"] = "Due now"
            else:
                mins = diff // 60
                item["status"] = f"Runs in {mins}m ({datetime.datetime.fromtimestamp(next_ts).strftime('%H:%M:%S')})"
            result.append(item)
        return result

    def get_due_jobs(self) -> List[Dict[str, Any]]:
        """Returns jobs that are ready to run."""
        now = time.time()
        due = []
        for j in self.jobs:
            if j.get("enabled", True) and j.get("next_run", 0) <= now:
                due.append(j)
        return due

    def mark_executed(self, job_id: str, success: bool = True, message: str = ""):
        """Updates last_run and recalculates next_run for a job."""
        now = time.time()
        for j in self.jobs:
            if j["id"] == job_id:
                j["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                j["run_count"] = j.get("run_count", 0) + 1
                j["last_status"] = "SUCCESS" if success else f"FAILED: {message}"

                if j.get("trigger_type") == "daily" and j.get("daily_time"):
                    target_h, target_m = map(int, j["daily_time"].split(":"))
                    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
                    target_dt = tomorrow.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
                    j["next_run"] = target_dt.timestamp()
                else:
                    interval = j.get("interval_seconds", 3600)
                    j["next_run"] = now + interval
                break
        self._save(self.jobs)
