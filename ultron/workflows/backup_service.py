from typing import Dict, Any, Optional
from ultron.tools.file_manager import FileManager
from ultron.tools.notifier import Notifier
from ultron.persona import get_quote

class BackupWorkflow:
    def __init__(self, file_manager: FileManager, notifier: Notifier):
        self.file_manager = file_manager
        self.notifier = notifier

    def run(self, source_directory: str, destination_directory: Optional[str] = None, prefix: str = "ultron_backup") -> Dict[str, Any]:
        """Executes a compressed snapshot backup of a directory."""
        self.notifier.info(f"Initiating state preservation for '{source_directory}'...")
        res = self.file_manager.backup_directory(source_directory, destination_directory, prefix=prefix)
        if res.get("success"):
            archive = res.get("archive_path")
            size_mb = res.get("archive_size_mb")
            count = res.get("total_files_archived")
            self.notifier.success(f"Snapshot secured: {archive} ({size_mb} MB, {count} files).")
            self.notifier.quote(get_quote("completion"))
        else:
            self.notifier.error(f"Backup failed: {res.get('error')}")
        return res
