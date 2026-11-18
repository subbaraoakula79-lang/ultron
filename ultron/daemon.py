import time
import sys
import signal
from pathlib import Path
from ultron.core import UltronCore
from ultron.workflows.auto_organizer import AutoOrganizerWorkflow
from ultron.workflows.health_guard import HealthGuardWorkflow
from ultron.workflows.backup_service import BackupWorkflow
from ultron.tools.notifier import ULTRON_BANNER, RED, GREEN, YELLOW, CYAN, RESET, BOLD
from ultron.persona import get_quote

class UltronDaemon:
    def __init__(self, config_path: str = "config.json"):
        self.core = UltronCore(config_path)
        self.notifier = self.core.notifier
        self.config = self.core.config
        self.running = False

        # Workflows
        self.health_guard = HealthGuardWorkflow(self.core.monitor, self.notifier)
        self.organizer = AutoOrganizerWorkflow(self.core.file_manager, self.notifier)
        self.backup_service = BackupWorkflow(self.core.file_manager, self.notifier)

    def _execute_job(self, job: dict):
        """Dispatches a due job based on its action."""
        action = job.get("action")
        args = job.get("args", {})
        job_id = job.get("id")
        name = job.get("name", action)

        self.notifier.info(f"Triggering scheduled directive: {name} [{action}]")

        try:
            if action == "health_check":
                cpu_th = args.get("cpu_thresh", self.config.get("automation.thresholds.cpu_percent_warning", 80.0))
                ram_th = args.get("ram_thresh", self.config.get("automation.thresholds.ram_percent_warning", 85.0))
                self.health_guard.run(cpu_thresh=cpu_th, ram_thresh=ram_th)
            elif action == "clean_temp":
                days = args.get("older_than_days", self.config.get("automation.temp_clean_older_than_days", 1.0))
                res = self.core.file_manager.clean_temp_files(older_than_days=days)
                self.notifier.info(f"Purged {res.get('files_purged', 0)} temp files ({res.get('space_reclaimed_mb', 0)} MB reclaimed).")
            elif action == "organize_downloads":
                target = args.get("path") or str(Path.home() / "Downloads")
                self.organizer.run_once(target)
            elif action == "backup":
                src = args.get("source", ".")
                dest = args.get("destination")
                self.backup_service.run(src, dest)
            elif action == "shell_cmd":
                cmd = args.get("command", "")
                if cmd:
                    res = self.core.executor.run(cmd)
                    self.notifier.info(f"Executed command '{cmd}': Exit code {res.get('exit_code')}")
            else:
                self.notifier.warning(f"Unrecognized scheduled action: {action}")

            self.core.scheduler.mark_executed(job_id, success=True)
        except Exception as e:
            self.notifier.error(f"Scheduled task failure for '{name}': {str(e)}")
            self.core.scheduler.mark_executed(job_id, success=False, message=str(e))

    def start(self):
        """Runs the main daemon loop."""
        print(ULTRON_BANNER)
        self.notifier.quote(get_quote("startup"))
        self.notifier.info("Ultron Background Automation Daemon initializing...")

        # Display active LLM provider status
        active_provider = self.core.provider_mgr.get_active_provider()
        if active_provider:
            self.notifier.success(f"Cognitive Engine: ACTIVE ({getattr(active_provider, 'model', 'default')})")
        else:
            self.notifier.warning("No live LLM provider detected (Ollama offline & no free API keys in config).")
            self.notifier.info("Operating in autonomous heuristic and scheduled task mode.")

        # Check watch paths
        if self.config.get("automation.auto_organize_downloads", False):
            watch_paths = self.config.get("automation.watch_paths", [str(Path.home() / "Downloads")])
            self.organizer.start_watching(watch_paths)

        # Initial health inspection
        self.health_guard.run()

        self.running = True
        tick_interval = self.config.get("automation.daemon_tick_interval_seconds", 5)
        self.notifier.info(f"Vigilance loop active. Scanning every {tick_interval}s. Press Ctrl+C to stop.")

        def shutdown_handler(signum, frame):
            print("\n")
            self.notifier.warning("Shutdown signal received. Releasing background vigilance...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, shutdown_handler)

        while self.running:
            try:
                due_jobs = self.core.scheduler.get_due_jobs()
                for job in due_jobs:
                    self._execute_job(job)
                time.sleep(tick_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.notifier.error(f"Daemon loop anomaly: {e}")
                time.sleep(tick_interval)

        self.stop()

    def stop(self):
        """Clean shutdown."""
        self.running = False
        self.organizer.stop_watching()
        self.notifier.info("Ultron Daemon terminated gracefully.")
