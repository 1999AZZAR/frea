import os
from src.tools import (
    bash_run,
    file_read,
    file_write,
    file_patch,
    grep_search,
    find_files,
)


def test_bash_run_success():
    result = bash_run("echo 'hello from frea'")
    assert result.success is True
    assert "hello from frea" in result.output


def test_bash_run_failure():
    result = bash_run("exit 42")
    assert result.success is False
    assert result.exit_code == 42


def test_bash_run_timeout():
    result = bash_run("sleep 5", timeout=1)
    assert result.success is False
    assert "timed out" in result.error.lower()


def test_file_write_and_read(tmp_path):
    target = tmp_path / "subdir" / "test.txt"
    # Write
    write_res = file_write(str(target), "line 1\nline 2\nline 3\n")
    assert write_res.success is True
    assert os.path.exists(target)

    # Read all
    read_res = file_read(str(target))
    assert read_res.success is True
    assert "line 1" in read_res.output
    assert "line 3" in read_res.output

    # Read sliced (lines 2 to 3)
    slice_res = file_read(str(target), start_line=2, end_line=3)
    assert slice_res.success is True
    assert "line 2" in slice_res.output
    assert "line 1" not in slice_res.output


def test_file_write_no_overwrite(tmp_path):
    target = tmp_path / "exists.txt"
    file_write(str(target), "initial")
    # Attempt overwrite without flag
    res = file_write(str(target), "new content", overwrite=False)
    assert res.success is False
    assert "already exists" in res.error.lower()


def test_file_patch(tmp_path):
    target = tmp_path / "patch_me.txt"
    file_write(str(target), "alpha\nbeta\ngamma\n")

    # Patch unique string
    patch_res = file_patch(str(target), target="beta", replacement="BETA_UPDATED")
    assert patch_res.success is True

    read_res = file_read(str(target))
    assert "BETA_UPDATED" in read_res.output
    assert "beta" not in read_res.output


def test_grep_and_find(tmp_path):
    file1 = tmp_path / "code1.py"
    file2 = tmp_path / "doc.txt"
    file_write(str(file1), "def target_func(): pass\n")
    file_write(str(file2), "Just some documentation text\n")

    # Grep
    grep_res = grep_search("target_func", path=str(tmp_path))
    assert grep_res.success is True
    assert "code1.py" in grep_res.output

    # Find
    find_res = find_files("*.py", path=str(tmp_path))
    assert find_res.success is True
    assert "code1.py" in find_res.output
    assert "doc.txt" not in find_res.output
