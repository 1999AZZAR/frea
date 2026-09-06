import time
from src.tools import (
    command_status,
    get_current_plan,
    run_command,
    stop_command,
    update_plan,
)


def test_run_command_foreground_success():
    res = run_command("echo 'Hello Frea'")
    assert res.success is True
    assert "Hello Frea" in res.output
    assert res.exit_code == 0


def test_run_command_foreground_failure():
    res = run_command("exit 42")
    assert res.success is False
    assert res.exit_code == 42


def test_run_command_foreground_timeout():
    res = run_command("sleep 5", timeout=1)
    assert res.success is False
    assert "timed out" in res.error.lower()


def test_run_command_background_lifecycle():
    # Start a quick background job
    res_start = run_command("echo 'bg work' && sleep 0.2", background=True)
    assert res_start.success is True
    assert "job-" in res_start.output
    job_id = [word for word in res_start.output.split() if word.startswith("job-")][0]

    # Poll status
    time.sleep(0.4)
    res_status = command_status(job_id)
    assert res_status.success is True
    assert "bg work" in res_status.output
    assert "completed" in res_status.output.lower()


def test_stop_command_background():
    # Start a long-running background job
    res_start = run_command("sleep 30", background=True)
    assert res_start.success is True
    job_id = [word for word in res_start.output.split() if word.startswith("job-")][0]

    # Stop the job
    res_stop = stop_command(job_id)
    assert res_stop.success is True
    assert (
        "stopped" in res_stop.output.lower() or "terminated" in res_stop.output.lower()
    )

    # Verify status reflects stopped
    res_status = command_status(job_id)
    assert res_status.success is True
    assert (
        "terminated" in res_status.output.lower()
        or "stopped" in res_status.output.lower()
    )


def test_update_plan_and_retrieve():
    plan = [
        {"step": "Explore repository", "status": "completed"},
        {"step": "Implement tooling", "status": "in_progress"},
        {"step": "Run test suite", "status": "pending"},
    ]
    res = update_plan(plan)
    assert res.success is True
    assert "3 steps" in res.output

    current = get_current_plan()
    assert len(current) == 3
    assert current[0]["step"] == "Explore repository"
    assert current[1]["status"] == "in_progress"


def test_update_plan_invalid():
    res = update_plan("not a list")  # type: ignore
    assert res.success is False
    assert "must be a list" in res.error.lower()
