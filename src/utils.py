import re
import subprocess
import time
from color import Color
import sys
import itertools


def cursor_hide():
    """Hide the cursor in the terminal"""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def cursor_show():
    """Show the cursor in the terminal"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def remove_emojis(text):
    """Remove emojis from the model response"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF"
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


def run_subprocess(command):
    """Run a subprocess command"""
    try:
        subprocess.run(command, shell=True)
    except Exception as e:
        """error handling"""
        print(
            f"{Color.BRIGHTYELLOW}\n╰─❯ {Color.ENDC}{Color.BRIGHTRED}subprocess execution error: {e}{Color.ENDC}"
        )


stop_loading = False


def set_stop_loading(value):
    global stop_loading
    stop_loading = value


def loading_animation(*args):
    """Show loading spinner while waiting for AI response."""
    cursor_hide()
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    try:
        while not stop_loading:
            sys.stdout.write(f'\r{Color.LIGHTPURPLE}{next(spinner)} Thinking...{Color.ENDC}')
            sys.stdout.flush()
            time.sleep(0.1)
    finally:
        cursor_show()
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
