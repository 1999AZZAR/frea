import os, subprocess, time, re, readline, termios, tty, sys, threading, configparser, datetime
from dotenv import load_dotenv
import google.generativeai as genai

class Color:
    """ANSI escape codes for terminal colors"""
    # Normal colors
    BLACK        = '\033[30m' # Black
    RED          = '\033[31m' # Red
    GREEN        = '\033[32m' # Green
    YELLOW       = '\033[33m' # Yellow
    BLUE         = '\033[34m' # Blue
    CYAN         = '\033[36m' # Cyan
    WHITE        = '\033[37m' # White
    PURPLE       = '\033[35m' # Purple

    # Bright colors
    BRIGHTBLACK  = '\033[90m' # Bright black
    BRIGHTRED    = '\033[91m' # Bright red
    BRIGHTGREEN  = '\033[92m' # Bright green
    BRIGHTYELLOW = '\033[93m' # Bright yellow
    BRIGHTBLUE   = '\033[94m' # Bright blue
    BRIGHTCYAN   = '\033[96m' # Bright cyan
    BRIGHTWHITE  = '\033[97m' # Bright white
    BRIGHTPURPLE = '\033[95m' # Bright purple

    # Dark colors
    DARKRED      = '\033[31;2m' # Dark red
    DARKGREEN    = '\033[32;2m' # Dark green
    DARKYELLOW   = '\033[33;2m' # Dark yellow
    DARKBLUE     = '\033[34;2m' # Dark blue
    DARKCYAN     = '\033[36;2m' # Dark cyan
    DARKPURPLE   = '\033[35;2m' # Dark purple

    # Light colors
    LIGHTRED     = '\033[91;1m' # Light red
    LIGHTGREEN   = '\033[92;1m' # Light green
    LIGHTYELLOW  = '\033[93;1m' # Light yellow
    LIGHTBLUE    = '\033[94;1m' # Light blue
    LIGHTCYAN    = '\033[96;1m' # Light cyan
    LIGHTPURPLE  = '\033[95;1m' # Light purple

    # Pastel colors
    PASTELPINK   = '\033[95m'   # Pastel pink
    PASTELBLUE   = '\033[94m'   # Pastel blue
    PASTELGREEN  = '\033[92m'   # Pastel green
    PASTELYELLOW = '\033[93m'   # Pastel yellow
    PASTELPURPLE = '\033[95;1m' # Pastel purple

    # End of color
    ENDC        = '\033[0m'     # End of color

def cursor_hide():
    """Hide the cursor in the terminal"""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def cursor_show():
    """Show the cursor in the terminal"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()

class GeminiChatConfig:
    """Special commands for chat"""
    EXIT_COMMAND        = 'exit'
    CLEAR_COMMAND       = 'clear'
    RESET_COMMAND       = 'reset'
    PRINT_COMMAND       = 'print'
    RECONFIGURE_COMMAND = 'reconfigure'
    HELP_COMMAND        = 'help'
    CONFIG_FILE         = 'config.ini'

    @staticmethod
    def initialize_config():
        """Initialize the config.ini file"""
        config = configparser.ConfigParser()
        if not os.path.exists(GeminiChatConfig.CONFIG_FILE):
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}No Configuration found. Creating configuration file.{Color.ENDC}\n")
            config['DEFAULT'] = {
                'API': input("Enter the API key: "),
                'LoadingStyle': input("Enter the loading style (e.g., L1): "),
                'InstructionFile': input("Enter the path to the instruction file: ")
            }
            with open(GeminiChatConfig.CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
                print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Configuration saved successfully!{Color.ENDC}\n")
        else:
            config.read(GeminiChatConfig.CONFIG_FILE)
        return config

    @staticmethod
    def reconfigure():
        """Reconfigure the settings"""
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'API': input("Enter the new API key: "),
            'LoadingStyle': input("Enter the new loading style (e.g., L1): "),
            'InstructionFile': input("Enter the new path to the instruction file: ")
        }
        with open(GeminiChatConfig.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Configuration updated successfully!{Color.ENDC}\n")
        multiline_mode = False
        return config

    @staticmethod
    def display_help():
        """Display help information"""
        help_text = f"""
        {Color.BRIGHTCYAN}Special Commands:{Color.ENDC}
        {Color.BRIGHTYELLOW}{GeminiChatConfig.EXIT_COMMAND}{Color.ENDC} - Exit the application
        {Color.BRIGHTYELLOW}{GeminiChatConfig.CLEAR_COMMAND}{Color.ENDC} - Clear the terminal screen
        {Color.BRIGHTYELLOW}{GeminiChatConfig.RESET_COMMAND}{Color.ENDC} - Reset the chat session
        {Color.BRIGHTYELLOW}{GeminiChatConfig.PRINT_COMMAND}{Color.ENDC} - Save the conversation log to a file
        {Color.BRIGHTYELLOW}{GeminiChatConfig.RECONFIGURE_COMMAND}{Color.ENDC} - Reconfigure the settings
        {Color.BRIGHTYELLOW}{GeminiChatConfig.HELP_COMMAND}{Color.ENDC} - Display this help information
        """
        print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{help_text}")

    @staticmethod
    def initialize_genai_api(api_key):
        """Load API key from config"""
        load_dotenv()
        genai.configure(api_key=api_key)

    @staticmethod
    def gemini_generation_config():
        """Configuration for the Gemini language model"""
        return {
            'max_output_tokens': 2048,
            'temperature': 0.90,
            'candidate_count': 1,
            'top_k': 35,
            'top_p': 0.65,
            'stop_sequences': []
        }

    @staticmethod
    def gemini_safety_settings():
        """Safety settings for the model"""
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

    @staticmethod
    def chat_instruction(instruction_file):
        """Read the instruction file"""
        with open(instruction_file, 'r') as file:
            return file.read()

    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        subprocess.run('clear', shell=True)

class GeminiChat:
    def __init__(self):
        config = GeminiChatConfig.initialize_config()
        self.api_key = config['DEFAULT']['API']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.instruction_file = config['DEFAULT']['InstructionFile']
        GeminiChatConfig.initialize_genai_api(self.api_key)
        readline.parse_and_bind("tab: complete")
        self.conversation_log = []  # Initialize conversation log

    def process_user_input(self):
        """Set delimiters for auto-completion and enable Vi editing mode"""
        readline.set_completer_delims(' \t\n=')
        readline.parse_and_bind("set editing-mode vi")

        try:
            """Prompt for user input"""
            question = input(f"{Color.BLUE}╭─ User \n╰─> {Color.ENDC}")
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt")
            return ""
        return question.strip().lower()

    def remove_emojis(self, text):
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

    def run_subprocess(self, command):
        """Run a subprocess command"""
        try:
            subprocess.run(command, shell=True)
        except Exception as e:
            """error handling"""
            print(f"{Color.BRIGHTYELLOW}\n╰─> {Color.ENDC}{Color.BRIGHTRED}subprocess execution error: {e}{Color.ENDC}")
            multiline_mode = False

    def initialize_chat(self):
        """Initialize the chat session"""
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        instruction = GeminiChatConfig.chat_instruction(self.instruction_file)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        """initiate chat model history"""
        chat = model.start_chat(history=[])
        return chat, instruction

    def generate_chat(self):
        """model generation response flow"""
        def loading_animation(use='L1'):
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
                    'L9': ([' 🔸 ', ' 🔹 ', ' 🔷 ', ' 🔶 '], 0.2)
                }
                if use in animations:
                    frames, delay = animations[use]
                    for frame in frames:
                        print(f"{Color.LIGHTPURPLE}\r{frame}Processing{Color.ENDC}", end="")
                        time.sleep(delay)
            cursor_show()
            print("\r" + " " * 20 + "\r", end="")
            multiline_mode = False

        try:
            chat, instruction = self.initialize_chat()
            user_input = ""
            multiline_mode = False

            while True:
                """multiline automation"""
                if multiline_mode:
                    print(f"{Color.BLUE}╰─> {Color.ENDC}", end="")
                else:
                    print(f"{Color.BLUE}╭─ User \n╰─> {Color.ENDC}", end="")
                user_input_line = input()
                if user_input_line.endswith("\\"):
                    user_input += user_input_line.rstrip("\\") + "\n"
                    multiline_mode = True
                    continue
                else:
                    user_input += user_input_line
                    multiline_mode = False

                """Handle special commands"""
                if user_input == GeminiChatConfig.EXIT_COMMAND:
                    print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}")
                    break
                elif user_input == GeminiChatConfig.RESET_COMMAND:
                    print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Resetting session...{Color.ENDC}")
                    time.sleep(0.5)
                    GeminiChatConfig.clear_screen()
                    chat, instruction = self.initialize_chat()
                    self.conversation_log = []
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == GeminiChatConfig.CLEAR_COMMAND:
                    GeminiChatConfig.clear_screen()
                    continue
                elif user_input == GeminiChatConfig.HELP_COMMAND:
                    GeminiChatConfig.display_help()
                    continue
                elif user_input == GeminiChatConfig.RECONFIGURE_COMMAND:
                    config = GeminiChatConfig.reconfigure()
                    self.api_key = config['DEFAULT']['API']
                    self.loading_style = config['DEFAULT']['LoadingStyle']
                    self.instruction_file = config['DEFAULT']['InstructionFile']
                    GeminiChatConfig.initialize_genai_api(self.api_key)
                    chat, instruction = self.initialize_chat()
                    self.conversation_log = []
                    multiline_mode = False
                    user_input = ""
                    continue
                elif user_input == GeminiChatConfig.PRINT_COMMAND:
                    """Save conversation log to a file"""
                    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    log_file_name = f"log_{current_datetime}.txt"
                    with open(log_file_name, "w") as file:
                        for line in self.conversation_log:
                            file.write(line + "\n")
                    print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Conversation log saved to {log_file_name}{Color.ENDC}\n")
                    multiline_mode = False
                    continue
                elif not user_input:
                    break
                elif user_input.startswith("run "):
                    """Run a subprocess command"""
                    command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}executing user command{Color.ENDC}')
                    self.run_subprocess(command)
                    multiline_mode = False
                    print(f'\n')
                else:
                    """Send user input to the language model and print the response"""
                    stop_loading = False
                    loading_thread = threading.Thread(target=loading_animation, args=(self.loading_style,))
                    loading_thread.start()

                    response = chat.send_message(instruction + user_input)

                    stop_loading = True
                    loading_thread.join()

                    sanitized_response = self.remove_emojis(response.text)
                    sanitized_response = sanitized_response.replace('*', '')
                    print(f'{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{sanitized_response}')
                    multiline_mode = False

                    """Log the conversation"""
                    self.conversation_log.append(f"User: {user_input}")
                    self.conversation_log.append(f"Frea: {sanitized_response}")

                user_input = ""
                multiline_mode = False

        except KeyboardInterrupt:
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}")

        except Exception as e:
            """error handling"""
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.BRIGHTRED}An unexpected error occurred: {e}{Color.ENDC}")
            multiline_mode = False
            stop_loading = True

if __name__ == "__main__":
    chat_app = GeminiChat()
    chat_app.generate_chat()
