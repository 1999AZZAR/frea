"""OpenCode-styled inline tool cards, diff visualizer, and permission prompts for Frea."""

from typing import Any, Dict, List
from src.ui import THEME, Theme, format_path


def render_tool_call(tool_name: str, args: Dict[str, Any], theme: Theme = THEME) -> str:
    """Render inline tool invocation banner matching OpenCode style."""
    if tool_name in ("run_command", "bash_run"):
        cmd = args.get("command", "")
        return f"[{theme.text}]$ {cmd}[/]"
    elif tool_name in ("read_file", "file_read"):
        path = format_path(str(args.get("path", "")))
        offset = args.get("offset")
        limit = args.get("limit")
        if offset is not None or limit is not None:
            slice_info = f" (L{offset or 1}+{limit or 'all'})"
            return f"[{theme.info}]→ Read {path}{slice_info}[/]"
        return f"[{theme.info}]→ Read {path}[/]"
    elif tool_name in ("write_file", "file_write"):
        path = format_path(str(args.get("path", "")))
        return f"[{theme.accent}]← Write {path}[/]"
    elif tool_name in ("patch_file", "file_patch"):
        path = format_path(str(args.get("path", "")))
        return f"[{theme.warning}]← Patched {path}[/]"
    elif tool_name in ("grep", "grep_search"):
        pattern = args.get("query") or args.get("pattern", "")
        path = format_path(str(args.get("path", ".")))
        return f'[{theme.secondary}]✱ Grep "{pattern}" in {path}[/]'
    elif tool_name in ("glob", "find_files"):
        pattern = args.get("pattern", "")
        path = format_path(str(args.get("path", ".")))
        return f'[{theme.secondary}]✱ Glob "{pattern}" in {path}[/]'
    elif tool_name == "list_directory":
        path = format_path(str(args.get("path", ".")))
        return f"[{theme.secondary}]✱ List {path}[/]"
    elif tool_name == "command_status":
        job_id = args.get("job_id", "")
        return f"[{theme.info}]⚙ Status job {job_id}[/]"
    elif tool_name == "stop_command":
        job_id = args.get("job_id", "")
        return f"[{theme.warning}]⚙ Stop job {job_id}[/]"
    elif tool_name == "update_plan":
        return f"[{theme.accent}]⚙ Update Plan[/]"
    elif tool_name == "skill":
        name = args.get("name", "")
        return f"[{theme.info}]→ Skill {name}[/]"
    elif tool_name.startswith("mcp__") or "_" in tool_name:
        return f"[{theme.secondary}]⚙ {tool_name} {args}[/]"
    return f"[{theme.text_muted}]⚙ {tool_name} {args}[/]"


def render_pending_tool_call(
    tool_name: str, args: Dict[str, Any], theme: Theme = THEME
) -> str:
    """Render OpenCode-style pending tool notification (~ Pending action...)."""
    if tool_name in ("run_command", "bash_run"):
        return f"[{theme.text_muted}]~ Running command…[/]"
    elif tool_name in ("read_file", "file_read"):
        return f"[{theme.text_muted}]~ Reading file…[/]"
    elif tool_name in ("write_file", "file_write"):
        return f"[{theme.text_muted}]~ Writing file…[/]"
    elif tool_name in ("patch_file", "file_patch"):
        return f"[{theme.text_muted}]~ Preparing edit…[/]"
    elif tool_name in ("grep", "grep_search"):
        return f"[{theme.text_muted}]~ Searching content…[/]"
    elif tool_name in ("glob", "find_files", "list_directory"):
        return f"[{theme.text_muted}]~ Finding files…[/]"
    elif tool_name == "update_plan":
        return f"[{theme.text_muted}]~ Updating plan…[/]"
    elif tool_name == "skill":
        return f"[{theme.text_muted}]~ Loading skill…[/]"
    return f"[{theme.text_muted}]~ Executing {tool_name}…[/]"


def render_unified_diff(diff_text: str, theme: Theme = THEME) -> str:
    """Syntax-highlight unified diff with OpenCode diff color scheme."""
    styled_lines = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            styled_lines.append(f"[{theme.text_muted}]{line}[/]")
        elif line.startswith("+"):
            styled_lines.append(f"[{theme.diff_added}]{line}[/]")
        elif line.startswith("-"):
            styled_lines.append(f"[{theme.diff_removed}]{line}[/]")
        elif line.startswith("@@"):
            styled_lines.append(f"[{theme.diff_context}]{line}[/]")
        else:
            styled_lines.append(f"[{theme.text}]{line}[/]")
    return "\n".join(styled_lines)


def render_plan_card(plan_items: List[Dict[str, Any]], theme: Theme = THEME) -> str:
    """Render OpenCode live todo / checklist card."""
    lines = [f"[{theme.accent} bold]Plan[/]"]
    for item in plan_items:
        step = item.get("step", "")
        status = item.get("status", "pending")
        if status == "completed":
            lines.append(f"  [{theme.success}]●[/] [{theme.text}]{step}[/]")
        elif status == "in_progress":
            lines.append(f"  [{theme.primary}]◐[/] [{theme.text} bold]{step}[/]")
        elif status == "failed":
            lines.append(f"  [{theme.error}]✕[/] [{theme.error}]{step}[/]")
        else:
            lines.append(f"  [{theme.text_muted}]○[/] [{theme.text_muted}]{step}[/]")
    return "\n".join(lines)


def render_tool_result(
    tool_name: str,
    args: Dict[str, Any],
    result: str,
    max_lines: int = 10,
    theme: Theme = THEME,
) -> str:
    """Render tool execution output with OpenCode collapsing and badges."""
    lines = result.splitlines()

    if tool_name in ("run_command", "bash_run"):
        cmd = args.get("command", "")
        header = (
            f"[{theme.text_muted}]# Running in terminal[/]\n[{theme.text}]$ {cmd}[/]"
        )
        if len(lines) > max_lines:
            truncated = "\n".join(lines[:max_lines])
            remaining = len(lines) - max_lines
            collapsed = (
                f"\n[{theme.text_muted}]↳ ... ({remaining} more lines collapsed)[/]"
            )
            return f"{header}\n{truncated}{collapsed}"
        return f"{header}\n{result}" if result else header

    elif tool_name in ("read_file", "file_read"):
        path = format_path(str(args.get("path", "")))
        count = len(lines)
        return f"[{theme.text_muted}]↳ Loaded {path} ({count} line{'s' if count != 1 else ''})[/]"

    elif tool_name in ("write_file", "file_write"):
        path = format_path(str(args.get("path", "")))
        count = len(lines)
        return f"[{theme.success}]# Wrote {path} ({count} line{'s' if count != 1 else ''})[/]"

    elif tool_name in ("patch_file", "file_patch"):
        path = format_path(str(args.get("path", "")))
        header = f"[{theme.success}]# Patched {path}[/]"
        if "+++" in result or "---" in result or "@@" in result:
            return f"{header}\n{render_unified_diff(result, theme)}"
        return f"{header}\n[{theme.text_muted}]↳ {result}[/]"

    elif tool_name in ("grep", "grep_search", "glob", "find_files"):
        non_empty = [line for line in lines if line.strip()]
        count = len(non_empty)
        badge = f"[{theme.text_muted}]↳ {count} match{'es' if count != 1 else ''}[/]"
        if len(lines) > max_lines:
            truncated = "\n".join(lines[:max_lines])
            remaining = len(lines) - max_lines
            collapsed = (
                f"\n[{theme.text_muted}]↳ ... ({remaining} more lines collapsed)[/]"
            )
            return f"{badge}\n{truncated}{collapsed}"
        return f"{badge}\n{result}" if result else badge

    elif tool_name == "list_directory":
        count = len(lines)
        badge = f"[{theme.text_muted}]↳ {count} entr{'ies' if count != 1 else 'y'}[/]"
        if len(lines) > max_lines:
            truncated = "\n".join(lines[:max_lines])
            remaining = len(lines) - max_lines
            collapsed = (
                f"\n[{theme.text_muted}]↳ ... ({remaining} more lines collapsed)[/]"
            )
            return f"{badge}\n{truncated}{collapsed}"
        return f"{badge}\n{result}" if result else badge

    elif tool_name == "update_plan":
        plan_data = args.get("plan", [])
        if isinstance(plan_data, list):
            return render_plan_card(plan_data, theme)
        return f"[{theme.success}]↳ {result}[/]"

    elif tool_name == "skill":
        name = args.get("name", "")
        return f"[{theme.success}]↳ Loaded skill '{name}'[/]"

    elif tool_name in ("command_status", "stop_command"):
        return f"[{theme.info}]↳ {result}[/]"

    return f"[{theme.text_muted}]↳ {result}[/]"


def render_permission_prompt(
    tool_name: str, args: Dict[str, Any], theme: Theme = THEME
) -> str:
    """Render interactive permission prompt asking user confirmation."""
    target = args.get("command") or args.get("path") or str(args)
    return f"[{theme.warning}]△ Permission needed:[/] Run [{theme.text}]{tool_name}[/] on [{theme.info}]{target}[/]? [y/N]: "


def render_response_card(
    response: str,
    collapsed: bool = False,
    peek_lines: int = 2,
    model: str = "",
    theme: Theme = THEME,
) -> str:
    """Render Assistant response matching Kamui's card design.

    Features:
      - Left thick rail ('▌ ') matching Kamui's THICK_BORDER
      - Header pill with model and fold control action ([▼ Collapse] / [▶ Expand])
      - Peek preview when collapsed (COLLAPSED_PEEK = 2 lines + '… N more line(s) · ctrl+o or /expand')
    """
    clean_resp = response.rstrip()
    if not clean_resp:
        return ""

    lines = clean_resp.splitlines()
    total_lines = len(lines)
    model_tag = f" [dim]({model})[/]" if model else ""
    rail = f"[{theme.primary}]▌[/]"

    if collapsed and total_lines > peek_lines:
        hidden = total_lines - peek_lines
        control_pill = (
            f"[{theme.text_muted}][▶ Expand (+{hidden} lines) · Ctrl+O / /expand][/]"
        )
        tag = f"{model_tag}   " if model_tag else ""
        header = f"\n{rail} {tag}{control_pill}"
        peek_body = "\n".join(f"{rail} {line}" for line in lines[:peek_lines])
        footer = (
            f"{rail} [{theme.text_muted}]… {hidden} more line(s) · ctrl+o or /expand[/]"
        )
        return f"{header}\n{peek_body}\n{footer}\n"
    else:
        control_pill = f"[{theme.text_muted}][▼ Collapse · Ctrl+O / /collapse][/]"
        tag = f"{model_tag}   " if model_tag else ""
        header = f"\n{rail} {tag}{control_pill}"
        body = "\n".join(f"{rail} {line}" for line in lines)
        return f"{header}\n{body}\n"
