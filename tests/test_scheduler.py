import pytest
from ultron.tools.scheduler import TaskScheduler


def test_task_scheduler_defaults(tmp_path):
    sched_file = tmp_path / "test_schedules.json"
    scheduler = TaskScheduler(str(sched_file))
    jobs = scheduler.list_jobs()
    assert len(jobs) >= 2
    action_names = [j["action"] for j in jobs]
    assert "health_check" in action_names
    assert "clean_temp" in action_names


def test_add_and_remove_job(tmp_path):
    sched_file = tmp_path / "custom_sched.json"
    scheduler = TaskScheduler(str(sched_file))

    added = scheduler.add_job(
        name="Test Backup",
        action="backup_folder",
        interval_seconds=7200,
        args={"path": "test"}
    )
    assert added["name"] == "Test Backup"
    job_id = added["id"]

    # Verify present
    assert any(j["id"] == job_id for j in scheduler.list_jobs())

    # Remove
    assert scheduler.remove_job(job_id) is True
    assert not any(j["id"] == job_id for j in scheduler.list_jobs())
