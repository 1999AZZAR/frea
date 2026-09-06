from src.cards import (
    render_permission_prompt,
    render_response_card,
    render_tool_call,
    render_tool_result,
    render_unified_diff,
)


def test_render_tool_call_inline():
    assert "$ ls -la" in render_tool_call("bash_run", {"command": "ls -la"})
    assert "$ ls -la" in render_tool_call("run_command", {"command": "ls -la"})
    assert "→ Read src/main.py" in render_tool_call(
        "file_read", {"path": "src/main.py"}
    )
    assert "→ Read src/main.py" in render_tool_call(
        "read_file", {"path": "src/main.py"}
    )
    assert "← Write src/main.py" in render_tool_call(
        "file_write", {"path": "src/main.py"}
    )
    assert "← Write src/main.py" in render_tool_call(
        "write_file", {"path": "src/main.py"}
    )
    assert "← Patched src/main.py" in render_tool_call(
        "file_patch", {"path": "src/main.py"}
    )
    assert "← Patched src/main.py" in render_tool_call(
        "patch_file", {"path": "src/main.py"}
    )
    assert '✱ Grep "foo"' in render_tool_call("grep_search", {"pattern": "foo"})
    assert '✱ Grep "foo"' in render_tool_call("grep", {"query": "foo"})
    assert '✱ Glob "*.py"' in render_tool_call("find_files", {"pattern": "*.py"})
    assert '✱ Glob "*.py"' in render_tool_call("glob", {"pattern": "*.py"})
    assert "→ Skill caveman" in render_tool_call("skill", {"name": "caveman"})
    assert "⚙ Update Plan" in render_tool_call("update_plan", {"plan": []})


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


def test_render_response_card():
    # Empty response
    assert render_response_card("") == ""
    assert render_response_card("   \n\n  ") == ""

    # Normal expanded response
    short_resp = "Line 1\nLine 2\nLine 3"
    card = render_response_card(short_resp, collapsed=False, model="openrouter/auto")
    assert "▌[/] [#fab283 bold]Assistant" in card
    assert "(openrouter/auto)" in card
    assert "▼ Collapse · Ctrl+O / /collapse" in card
    assert "▌[/] Line 1" in card
    assert "▌[/] Line 2" in card
    assert "▌[/] Line 3" in card

    # Collapsed response with > 2 lines (Kamui default peek is 2)
    long_resp = "\n".join([f"Line {i}" for i in range(10)])
    collapsed_card = render_response_card(
        long_resp, collapsed=True, peek_lines=2, model="openrouter/auto"
    )
    assert "Assistant" in collapsed_card
    assert "▶ Expand (+8 lines) · Ctrl+O / /expand" in collapsed_card
    assert "▌[/] Line 0" in collapsed_card
    assert "▌[/] Line 1" in collapsed_card
    assert "▌[/] Line 2" not in collapsed_card
    assert "… 8 more line(s) · ctrl+o or /expand" in collapsed_card
