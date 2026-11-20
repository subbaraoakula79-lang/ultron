import os
from pathlib import Path
import pytest
from ultron.tools.desktop.app_launcher import AppLauncher
from ultron.tools.desktop.desktop_controller import DesktopController


def test_app_launcher_allowlist():
    launcher = AppLauncher()
    apps = launcher.list_supported_apps()
    assert "calc" in apps
    assert "notepad" in apps
    assert "code" in apps
    assert "chrome" in apps


def test_desktop_controller_system_status():
    controller = DesktopController()
    status = controller.get_system_status()
    assert status["success"] is True
    assert "ram_total_mb" in status
    assert "ram_free_mb" in status
    assert "cpu_percent" in status


def test_search_and_read_files(tmp_path):
    controller = DesktopController()
    test_file = tmp_path / "sample_report.txt"
    test_file.write_text("Ultron Autonomous Agent System Report\nLine 2 info\nLine 3 conclusion", encoding="utf-8")

    search_res = controller.search_files(str(tmp_path), "sample")
    assert search_res["success"] is True
    assert search_res["count"] == 1
    assert search_res["matches"][0]["name"] == "sample_report.txt"

    read_res = controller.read_text_file(str(test_file), max_lines=2)
    assert read_res["success"] is True
    assert read_res["lines_read"] == 2
    assert "Ultron Autonomous" in read_res["content"]


def test_preview_organize_downloads_no_mutation(tmp_path):
    controller = DesktopController()
    f1 = tmp_path / "document.pdf"
    f2 = tmp_path / "photo.png"
    f1.write_text("pdf dummy", encoding="utf-8")
    f2.write_text("png dummy", encoding="utf-8")

    preview = controller.preview_organize_downloads(str(tmp_path))
    assert preview["success"] is True
    assert preview["files_to_organize"] == 2

    # Verify files were NOT moved or deleted during preview
    assert f1.exists()
    assert f2.exists()
