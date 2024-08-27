import re
import subprocess
import time
from color import Color
import sys
from fpdf import FPDF
from chat_config import ChatConfig
import json

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
    emoji_pattern = re.compile("["
                                u"\U0001F600-\U0001F64F"
                                u"\U0001F300-\U0001F5FF"
                                u"\U0001F680-\U0001F6FF"
                                u"\U0001F1E0-\U0001F1FF"
                                u"\U00002500-\U00002BEF"
                                u"\U00002702-\U000027B0"
                                u"\U00002702-\U000027B0"
                                u"\U000024C2-\U0001F251"
                                u"\U0001f926-\U0001f937"
                                u"\U00010000-\U0010ffff"
                                u"\u2640-\u2642"
                                u"\u2600-\u2B55"
                                u"\u200d"
                                u"\u23cf"
                                u"\u23e9"
                                u"\u231a"
                                u"\ufe0f"
                                u"\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def run_subprocess(command):
    """Run a subprocess command"""
    try:
        subprocess.run(command, shell=True)
    except Exception as e:
        """error handling"""
        print(f"{Color.BRIGHTYELLOW}\n╰─❯ {Color.ENDC}{Color.BRIGHTRED}subprocess execution error: {e}{Color.ENDC}")

stop_loading = False
def set_stop_loading(value):
    global stop_loading
    stop_loading = value

def loading_animation(use='L2'):
    """loading animation"""
    cursor_hide()
    while not stop_loading:
        animations = {
            'L0': ([' 🙉 ', ' 🙈 ', ' 🙊 ', ' 🙈 '], 0.2),
            'L1': ([' ∙∙∙∙∙ ', ' ●∙∙∙∙ ', ' ∙●∙∙∙ ', ' ∙∙●∙∙ ', ' ∙∙∙●∙ ', ' ∙∙∙∙● '], 0.1),
            'L2': ([' ⣾ ', ' ⣽ ', ' ⣻ ', ' ⢿ ', ' ⡿ ', ' ⣟ ', ' ⣯ ', ' ⣷ '], 0.15),
            'L3': ([' 🌑 ', ' 🌒 ', ' 🌓 ', ' 🌔 ', ' 🌕 ', ' 🌖 ', ' 🌗 ', ' 🌘 '], 0.22),
            'L4': ([' ◐ ', ' ◓ ', ' ◑ ', ' ◒ '], 0.1),
            'L5': ([' ▖ ', ' ▘ ', ' ▝ ', ' ▗ '], 0.2),
            'L6': ([' ⠁ ', ' ⠂ ', ' ⠄ ', ' ⡀ ', ' ⢀ ', ' ⠠ ', ' ⠐ ', ' ⠈ '], 0.15),
            'L7': ([' ⣀ ', ' ⣤ ', ' ⣶ ', ' ⣾ ', ' ⣿ ', ' ⣷ ', ' ⣯ ', ' ⣟ '], 0.2),
            'L8': ([' 🕛 ', ' 🕐 ', ' 🕑 ', ' 🕒 ', ' 🕓 ', ' 🕔 ', ' 🕕 ', ' 🕖 ', ' 🕗 ', ' 🕘 ', ' 🕙 ', ' 🕚 '], 0.15),
            'L9': ([' 🔸 ', ' 🔹 ', ' 🔷 ', ' 🔶 '], 0.2),
            'L10': ([' .    ',' ..   ',' ...  ',' .... '], 0.15)
        }
        if use in animations:
            frames, delay = animations[use]
            for frame in frames:
                print(f"{Color.LIGHTPURPLE}\r{frame}Processing{Color.ENDC}", end="")
                time.sleep(delay)
    cursor_show()
    print("\r" + " " * 20 + "\r", end="")

def save_log(log_file_name, chat_history):
    """Save conversation log to a JSON file"""
    log_file_name = f"{ChatConfig.LOG_FOLDER}/{log_file_name}.json"
    with open(log_file_name, "w") as file:
        json.dump(chat_history, file, indent=4)
    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation history saved to {log_file_name}{Color.ENDC}\n")

def print_log(log_file_name, chat_history):
    """Save conversation log to a PDF file"""
    log_file_name = f"{ChatConfig.LOG_FOLDER}/{log_file_name}.pdf"
    pdf = FPDF()

    # Title Page
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(0, 10, 'Conversation Log', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Log File: {log_file_name}", ln=True, align='C')
    pdf.cell(0, 10, f"Date: {time.strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(20)

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for entry in chat_history:
        role = entry.get("role", "unknown")
        parts = entry.get("parts", [])

        # Title for each new section
        if role == "user":
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(0, 10, 'User:', ln=True)
        elif role == "model":
            pdf.set_font("Arial", style='B', size=12)
            pdf.cell(0, 10, 'Model:', ln=True)
        else:
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 10, 'Unknown Role:', ln=True)

        pdf.set_font("Arial", size=11)

        for part in parts:

            # Set color based on role
            if role == "user":
                pdf.set_text_color(0, 0, 255)  # Blue for user
            elif role == "model":
                pdf.set_text_color(0, 128, 0)  # Green for model
            else:
                pdf.set_text_color(0, 0, 0)  # Black for unknown

            pdf.multi_cell(0, 10, part)
            pdf.ln(5)  # Add space after each part

    pdf.output(log_file_name)
    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation history saved to {log_file_name}{Color.ENDC}\n")
