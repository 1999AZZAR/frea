from typing import Any
from src.ui import THEME, Theme, format_path


def render_tool_call(tool_name: str, args: dict[str, Any], theme: Theme = THEME) -> str:
    if tool_name == "bash_run":
        cmd = args.get("command", "")
        return f"[{theme.text}]$ {cmd}[/]"
    elif tool_name == "file_read":
        path = format_path(str(args.get("path", "")))
        return f"[{theme.info}]→ Read {path}[/]"
    elif tool_name == "file_write":
        path = format_path(str(args.get("path", "")))
        return f"[{theme.accent}]← Write {path}[/]"
    elif tool_name == "file_patch":
        path = format_path(str(args.get("path", "")))
        return f"[{theme.warning}]← Patched {path}[/]"
    elif tool_name == "grep_search":
        pattern = args.get("pattern", "")
        path = format_path(str(args.get("path", ".")))
        return f'[{theme.secondary}]✱ Grep "{pattern}" in {path}[/]'
    elif tool_name == "find_files":
        pattern = args.get("pattern", "")
        path = format_path(str(args.get("path", ".")))
        return f'[{theme.secondary}]✱ Glob "{pattern}" in {path}[/]'
    return f"[{theme.text_muted}]⚙ {tool_name} {args}[/]"


def render_unified_diff(diff_text: str, theme: Theme = THEME) -> str:
    styled_lines = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            styled_lines.append(f"[{theme.text_muted}]{line}[/]")
        elif line.startswith("+"):
            styled_lines.append(f"[{theme.diff_added}]{line}[/]")
        elif line.startswith("-"):
            styled_lines.append(f"[{theme.diff_removed}]{line}[/]")
        elif line.startswith("@@"):
            styled_lines.append(f"[{theme.accent}]{line}[/]")
        else:
            styled_lines.append(f"[{theme.text}]{line}[/]")
    return "\n".join(styled_lines)


def render_tool_result(
    tool_name: str,
    args: dict[str, Any],
    result: str,
    max_lines: int = 10,
    theme: Theme = THEME,
) -> str:
    lines = result.splitlines()

    if tool_name == "bash_run":
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

    elif tool_name == "file_read":
        path = format_path(str(args.get("path", "")))
        count = len(lines)
        return f"[{theme.text_muted}]↳ Loaded {path} ({count} line{'s' if count != 1 else ''})[/]"

    elif tool_name == "file_write":
        path = format_path(str(args.get("path", "")))
        count = len(lines)
        return f"[{theme.success}]# Wrote {path} ({count} line{'s' if count != 1 else ''})[/]"

    elif tool_name == "file_patch":
        path = format_path(str(args.get("path", "")))
        header = f"[{theme.success}]# Patched {path}[/]"
        if "+++" in result or "---" in result or "@@" in result:
            return f"{header}\n{render_unified_diff(result, theme)}"
        return f"{header}\n[{theme.text_muted}]↳ {result}[/]"

    elif tool_name in ("grep_search", "find_files"):
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

    return f"[{theme.text_muted}]↳ {result}[/]"


def render_permission_prompt(
    tool_name: str, args: dict[str, Any], theme: Theme = THEME
) -> str:
    target = args.get("command") or args.get("path") or str(args)
    return f"[{theme.warning}]△ Permission needed:[/] Run [{theme.text}]{tool_name}[/] on [{theme.info}]{target}[/]? [y/N]: "
