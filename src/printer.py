import json
from pathlib import Path
from chat_config import ChatConfig
from color import Color


def save_log(log_file_name, chat_history):
    """
    Saves the conversation log to a JSON file.

    Args:
        log_file_name (str): The name of the file to save the log to.
        chat_history (list): The chat history to save.
    """
    # Ensure export directory exists
    export_dir = Path(ChatConfig.EXPORT_FOLDER)
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / f"{log_file_name}.json"
    with open(filepath, "w") as file:
        json.dump(chat_history, file, indent=4)
    print(
        f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation history saved to {filepath}{Color.ENDC}\n"
    )


def format_markdown(chat_history):
    """
    Formats the chat history into Markdown syntax.

    Args:
        chat_history (list): The chat history to format.

    Returns:
        str: The formatted Markdown content.
    """
    markdown_content = "# Conversation Log\n\n"
    for entry in chat_history:
        role = entry.get("role", "unknown")
        content = entry.get("content", "")

        if role == "user":
            markdown_content += "## User:\n"
        elif role == "assistant":
            markdown_content += "## Assistant:\n"
        else:
            markdown_content += f"## {role.capitalize()}:\n"

        markdown_content += f"{content}\n\n"
    return markdown_content


def save_markdown(log_file_name, chat_history):
    """
    Saves the conversation log to a Markdown file.

    Args:
        log_file_name (str): The name of the file to save the log to.
        chat_history (list): The chat history to save.
    """
    # Ensure export directory exists
    export_dir = Path(ChatConfig.EXPORT_FOLDER)
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / f"{log_file_name}.md"
    markdown_content = format_markdown(chat_history)

    with open(filepath, "w") as file:
        file.write(markdown_content)

    print(
        f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation history saved to {filepath}{Color.ENDC}\n"
    )


def print_log(log_file_name, chat_history):
    """
    Saves the conversation log to a Markdown file.

    Args:
        log_file_name (str): The name of the file to save the log to.
        chat_history (list): The chat history to save.
    """
    save_markdown(log_file_name, chat_history)
