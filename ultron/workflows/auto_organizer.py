import time
from pathlib import Path
from typing import List, Optional
from ultron.tools.file_manager import FileManager
from ultron.tools.notifier import Notifier
from ultron.persona import get_quote

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

class OrganizerFileHandler(FileSystemEventHandler):
    def __init__(self, organizer: 'AutoOrganizerWorkflow', watch_dir: Path):
        self.organizer = organizer
        self.watch_dir = watch_dir
        self.last_run = 0

    def on_created(self, event):
        if event.is_directory:
            return
        # Debounce: wait 2 seconds after creation to ensure writing completes
        now = time.time()
        if now - self.last_run > 2.0:
            self.last_run = now
            # Run organization after short delay
            time.sleep(1.0)
            self.organizer.run_once(str(self.watch_dir))

class AutoOrganizerWorkflow:
    def __init__(self, file_manager: FileManager, notifier: Notifier):
        self.file_manager = file_manager
        self.notifier = notifier
        self.observer = None
        self.is_watching = False

    def run_once(self, target_directory: str) -> dict:
        """Runs a single pass file organization on target directory."""
        res = self.file_manager.organize_directory(target_directory)
        count = res.get("total_files_organized", 0)
        if count > 0:
            self.notifier.info(f"Organized {count} files in '{target_directory}'.")
            self.notifier.quote(get_quote("cleanup"))
        return res

    def start_watching(self, watch_paths: List[str]):
        """Starts real-time folder monitoring with watchdog."""
        if not WATCHDOG_AVAILABLE:
            self.notifier.warning("Watchdog not available. Falling back to periodic interval checks.")
            return

        if self.is_watching:
            return

        self.observer = Observer()
        valid_paths = 0
        for p in watch_paths:
            path_obj = Path(p).resolve()
            if path_obj.exists() and path_obj.is_dir():
                handler = OrganizerFileHandler(self, path_obj)
                self.observer.schedule(handler, str(path_obj), recursive=False)
                valid_paths += 1
                self.notifier.info(f"Vigilance active: Watching directory '{path_obj}' for file chaos.")

        if valid_paths > 0:
            self.observer.start()
            self.is_watching = True

    def stop_watching(self):
        """Stops watchdog observer."""
        if self.observer and self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            self.notifier.info("Folder vigilance deactivated.")
