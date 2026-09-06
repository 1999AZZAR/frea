from src.cards import (
    render_permission_prompt,
    render_tool_call,
    render_tool_result,
    render_unified_diff,
)


def test_render_tool_call_inline():
    assert "$ ls -la" in render_tool_call("bash_run", {"command": "ls -la"})
    assert "→ Read src/main.py" in render_tool_call(
        "file_read", {"path": "src/main.py"}
    )
    assert "← Write src/main.py" in render_tool_call(
        "file_write", {"path": "src/main.py"}
    )
    assert "← Patched src/main.py" in render_tool_call(
        "file_patch", {"path": "src/main.py"}
    )
    assert '✱ Grep "foo"' in render_tool_call("grep_search", {"pattern": "foo"})
    assert '✱ Glob "*.py"' in render_tool_call("find_files", {"pattern": "*.py"})


def test_render_tool_result_bash_collapse():
    # Long output should collapse beyond 10 lines
    lines = [f"line {i}" for i in range(25)]
    output = "\n".join(lines)
    rendered = render_tool_result(
        "bash_run", {"command": "seq 25"}, output, max_lines=10
    )
    assert "$ seq 25" in rendered
    assert "line 0" in rendered
    assert "15 more lines" in rendered.lower() or "collapsed" in rendered.lower()


def test_render_unified_diff():
    diff_text = """--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,3 @@
-old line
+new line
 unchanged"""
    rendered = render_unified_diff(diff_text)
    assert "new line" in rendered
    assert "old line" in rendered


def test_render_permission_prompt():
    prompt = render_permission_prompt("bash_run", {"command": "rm -rf tmp"})
    assert "△" in prompt
    assert "Permission" in prompt
    assert "rm -rf tmp" in prompt
