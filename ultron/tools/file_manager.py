import os
import shutil
import time
import zipfile
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

EXT_CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xlsx", ".xls", ".csv", ".pptx", ".ppt", ".md"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "Media": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".mp3", ".wav", ".aac", ".flac", ".ogg"],
    "Code_and_Data": [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".yml", ".sql", ".sh", ".ps1", ".bat"],
    "Executables": [".exe", ".msi", ".iso", ".apk", ".bin"]
}

class FileManager:
    def __init__(self):
        pass

    def organize_directory(self, target_path: str, dry_run: bool = False) -> Dict[str, Any]:
        """Organizes loose files in target directory into categorized folders."""
        target = Path(target_path).resolve()
        if not target.exists() or not target.is_dir():
            return {"success": False, "error": f"Directory not found: {target_path}"}

        category_folders = set(EXT_CATEGORIES.keys())
        category_folders.add("Other")

        stats = {cat: 0 for cat in category_folders}
        total_moved = 0
        moved_files = []

        # Iterate only top-level files in the directory
        for item in target.iterdir():
            if item.is_dir():
                continue
            if item.name.startswith("."):
                continue  # skip hidden/system files

            ext = item.suffix.lower()
            assigned_cat = "Other"
            for cat, extensions in EXT_CATEGORIES.items():
                if ext in extensions:
                    assigned_cat = cat
                    break

            dest_folder = target / assigned_cat
            if not dry_run and not dest_folder.exists():
                dest_folder.mkdir(parents=True, exist_ok=True)

            dest_file = dest_folder / item.name
            # Resolve name conflicts
            counter = 1
            stem = item.stem
            while dest_file.exists():
                dest_file = dest_folder / f"{stem}_{counter}{item.suffix}"
                counter += 1

            if not dry_run:
                try:
                    shutil.move(str(item), str(dest_file))
                    stats[assigned_cat] += 1
                    total_moved += 1
                    moved_files.append({"from": item.name, "category": assigned_cat})
                except Exception as e:
                    print(f"[!] Warning: Could not move {item.name}: {e}")
            else:
                stats[assigned_cat] += 1
                total_moved += 1
                moved_files.append({"from": item.name, "category": assigned_cat})

        # Remove zero count categories from stats
        active_stats = {k: v for k, v in stats.items() if v > 0}

        return {
            "success": True,
            "target": str(target),
            "dry_run": dry_run,
            "total_files_organized": total_moved,
            "summary_by_category": active_stats,
            "details": moved_files[:50]  # sample of moved files
        }

    def clean_temp_files(self, extra_paths: Optional[List[str]] = None, older_than_days: float = 1.0) -> Dict[str, Any]:
        """Cleans temporary files and cache directories older than specified days."""
        targets = []
        win_temp = os.environ.get("TEMP")
        if win_temp and os.path.exists(win_temp):
            targets.append(Path(win_temp))

        if extra_paths:
            for p in extra_paths:
                p_path = Path(p)
                if p_path.exists():
                    targets.append(p_path)

        cutoff_time = time.time() - (older_than_days * 86400)
        files_deleted = 0
        bytes_reclaimed = 0
        errors = 0

        for target in targets:
            try:
                for root, dirs, files in os.walk(target, topdown=False):
                    for name in files:
                        file_path = os.path.join(root, name)
                        try:
                            stat = os.stat(file_path)
                            if stat.st_mtime < cutoff_time:
                                size = stat.st_size
                                os.remove(file_path)
                                files_deleted += 1
                                bytes_reclaimed += size
                        except (PermissionError, FileNotFoundError, OSError):
                            errors += 1
                            continue

                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        try:
                            # Try removing empty dirs
                            if not os.listdir(dir_path):
                                os.rmdir(dir_path)
                        except (PermissionError, OSError):
                            continue
            except Exception:
                continue

        reclaimed_mb = round(bytes_reclaimed / (1024 * 1024), 2)
        return {
            "success": True,
            "files_purged": files_deleted,
            "space_reclaimed_mb": reclaimed_mb,
            "locked_files_skipped": errors,
            "scanned_targets": [str(t) for t in targets]
        }

    def backup_directory(self, source_path: str, backup_dir: Optional[str] = None, prefix: str = "ultron_backup") -> Dict[str, Any]:
        """Creates a timestamped ZIP archive backup of the specified directory."""
        source = Path(source_path).resolve()
        if not source.exists():
            return {"success": False, "error": f"Source directory does not exist: {source_path}"}

        out_dir = Path(backup_dir).resolve() if backup_dir else source.parent / "Ultron_Backups"
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{prefix}_{source.name}_{timestamp}.zip"
        zip_filepath = out_dir / zip_filename

        file_count = 0
        try:
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source):
                    # Do not include the backup directory inside itself
                    if out_dir.resolve() in Path(root).resolve().parents or Path(root).resolve() == out_dir.resolve():
                        continue
                    for file in files:
                        full_path = Path(root) / file
                        arcname = full_path.relative_to(source)
                        try:
                            zipf.write(full_path, arcname)
                            file_count += 1
                        except (PermissionError, OSError):
                            continue

            archive_size_mb = round(zip_filepath.stat().st_size / (1024 * 1024), 2)
            return {
                "success": True,
                "archive_path": str(zip_filepath),
                "total_files_archived": file_count,
                "archive_size_mb": archive_size_mb,
                "timestamp": timestamp
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def find_large_files(self, target_dir: str, min_size_mb: float = 100.0, limit: int = 15) -> Dict[str, Any]:
        """Locates files consuming significant disk space."""
        target = Path(target_dir).resolve()
        if not target.exists():
            return {"success": False, "error": f"Target path does not exist: {target_dir}"}

        min_bytes = min_size_mb * 1024 * 1024
        large_files = []

        try:
            for root, _, files in os.walk(target):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        if sz >= min_bytes:
                            large_files.append({
                                "path": fp,
                                "name": f,
                                "size_mb": round(sz / (1024 * 1024), 2)
                            })
                    except (PermissionError, OSError):
                        continue
        except Exception as e:
            return {"success": False, "error": str(e)}

        large_files.sort(key=lambda x: x["size_mb"], reverse=True)
        return {
            "success": True,
            "target": str(target),
            "files_found": len(large_files),
            "top_files": large_files[:limit]
        }
