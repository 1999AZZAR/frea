from unittest.mock import MagicMock
from src.executor import ToolExecutor


def test_executor_read_safe_tools():
    """Safe tools like find_files or file_read execute without confirmation."""
    confirm_mock = MagicMock()
    executor = ToolExecutor(auto_approve=False, confirm_fn=confirm_mock)

    result = executor.execute("find_files", {"pattern": "*.py", "path": "."})
    assert result.success is True
    confirm_mock.assert_not_called()


def test_executor_destructive_prompt_approved(tmp_path):
    """Destructive tools call confirm_fn when auto_approve=False."""
    confirm_mock = MagicMock(return_value=True)
    executor = ToolExecutor(auto_approve=False, confirm_fn=confirm_mock)

    target_file = str(tmp_path / "test.txt")
    result = executor.execute("file_write", {"path": target_file, "content": "hello"})
    assert result.success is True
    confirm_mock.assert_called_once()


def test_executor_destructive_prompt_rejected(tmp_path):
    """If user rejects confirmation, tool execution is blocked."""
    confirm_mock = MagicMock(return_value=False)
    executor = ToolExecutor(auto_approve=False, confirm_fn=confirm_mock)

    target_file = str(tmp_path / "rejected.txt")
    result = executor.execute("file_write", {"path": target_file, "content": "blocked"})
    assert result.success is False
    assert "rejected" in result.error.lower()


def test_executor_auto_approve():
    """When auto_approve is True, confirmation prompt is bypassed."""
    confirm_mock = MagicMock()
    executor = ToolExecutor(auto_approve=True, confirm_fn=confirm_mock)

    result = executor.execute("bash_run", {"command": "echo 'auto-approved'"})
    assert result.success is True
    assert "auto-approved" in result.output
    confirm_mock.assert_not_called()


def test_executor_unknown_tool():
    executor = ToolExecutor(auto_approve=True)
    result = executor.execute("non_existent_tool", {})
    assert result.success is False
    assert "unknown tool" in result.error.lower()
