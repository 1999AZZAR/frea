import os, subprocess, time, re, readline, termios, tty, sys, threading, configparser, datetime, json
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
    LOG_FOLDER          = 'logs'

    DEFAULT_LOADING_STYLE = 'L2'
    DEFAULT_INSTRUCTION_FILE = './instructions/general.txt'
    DEFAULT_MODEL_NAME = 'gemini-1.5-pro'

    @staticmethod
    def initialize_config():
        """Initialize the config.ini file"""
        config = configparser.ConfigParser()
        if not os.path.exists(GeminiChatConfig.CONFIG_FILE):
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}No Configuration found. Creating configuration file.{Color.ENDC}\n")
            config['DEFAULT'] = {
                'API': input("Enter the API key: "),
                'LoadingStyle': input(f"Enter the loading style (e.g., L1, random, or press Enter for default '{GeminiChatConfig.DEFAULT_LOADING_STYLE}'): ") or GeminiChatConfig.DEFAULT_LOADING_STYLE,
                'InstructionFile': input(f"Enter the path to the instruction file (or press Enter for default '{GeminiChatConfig.DEFAULT_INSTRUCTION_FILE}'): ") or GeminiChatConfig.DEFAULT_INSTRUCTION_FILE,
                'ModelName': input(f"Enter the model name (or press Enter for default '{GeminiChatConfig.DEFAULT_MODEL_NAME}'): ") or GeminiChatConfig.DEFAULT_MODEL_NAME
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
                'API': input("Enter the API key: "),
                'LoadingStyle': input(f"Enter the loading style (e.g., L1, random, or press Enter for default '{GeminiChatConfig.DEFAULT_LOADING_STYLE}'): ") or GeminiChatConfig.DEFAULT_LOADING_STYLE,
                'InstructionFile': input(f"Enter the path to the instruction file (or press Enter for default '{GeminiChatConfig.DEFAULT_INSTRUCTION_FILE}'): ") or GeminiChatConfig.DEFAULT_INSTRUCTION_FILE,
                'ModelName': input(f"Enter the model name (or press Enter for default '{GeminiChatConfig.DEFAULT_MODEL_NAME}'): ") or GeminiChatConfig.DEFAULT_MODEL_NAME
            }
        with open(GeminiChatConfig.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Configuration updated successfully!{Color.ENDC}\n")
        return config

    @staticmethod
    def display_help():
        """Display help information"""
        help_text = f"""
    {Color.BRIGHTPURPLE}▒▓████████▓▒ ▒▓███████▓▒  ▒▓████████▓▒  ▒▓██████▓▒{Color.ENDC}
    {Color.BRIGHTPURPLE}▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒ ▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒{Color.ENDC}
    {Color.BRIGHTPURPLE}▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒ ▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒{Color.ENDC}
    {Color.BRIGHTPURPLE}▒▓██████▓▒   ▒▓███████▓▒  ▒▓██████▓▒   ▒▓████████▓▒{Color.ENDC}
    {Color.BRIGHTPURPLE}▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒ ▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒{Color.ENDC}
    {Color.BRIGHTPURPLE}▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒ ▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒{Color.ENDC}
    {Color.BRIGHTPURPLE}▒▓█▓▒        ▒▓█▓▒  ▒▓█▓▒ ▒▓████████▓▒ ▒▓█▓▒  ▒▓█▓▒{Color.ENDC}
    {Color.RED}Freak        Robotic      Entity with  Amusement{Color.ENDC}\n
    {Color.BRIGHTCYAN}Command List:{Color.ENDC}
    {Color.BRIGHTGREEN}{GeminiChatConfig.HELP_COMMAND}{Color.ENDC}  - Display this help information.
    {Color.BRIGHTGREEN}{GeminiChatConfig.EXIT_COMMAND}{Color.ENDC}  - Exit the application.
    {Color.BRIGHTGREEN}{GeminiChatConfig.CLEAR_COMMAND}{Color.ENDC} - Clear the terminal screen.
    {Color.BRIGHTGREEN}{GeminiChatConfig.RESET_COMMAND}{Color.ENDC} - Reset the chat session.
    {Color.BRIGHTGREEN}{GeminiChatConfig.PRINT_COMMAND}{Color.ENDC} - Save the conversation log to a file.
    {Color.BRIGHTGREEN}{GeminiChatConfig.RECONFIGURE_COMMAND}{Color.ENDC}   - Reconfigure the settings.
    {Color.BRIGHTGREEN}run (command){Color.ENDC} - run subprocess command eg run ls.
        """
        print(f"\n{help_text}")

    @staticmethod
    def initialize_genai_api(api_key):
        """Load API key from config"""
        genai.configure(api_key=api_key)

    @staticmethod
    def gemini_generation_config():
        """Configuration for the Gemini language model"""
        return {
            'max_output_tokens': 1024, # max 2048
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
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
        ]

    @staticmethod
    def chat_instruction(instruction_file):
        """Load instructions from the file"""
        if os.path.exists(instruction_file):
            with open(instruction_file, 'r') as file:
                return file.read()
        else:
            print(f"{Color.BRIGHTRED}Instruction file not found. Using default instructions.{Color.ENDC}")
            return "You are Frea (freak robotic entity with amusement), a helpful assistant."

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
        self.model_name = config['DEFAULT']['ModelName']
        GeminiChatConfig.initialize_genai_api(self.api_key)
        readline.parse_and_bind("tab: complete")
        self.conversation_log = []  # Initialize conversation log
        self.log_folder = GeminiChatConfig.LOG_FOLDER

    def process_user_input(self):
        """Set delimiters for auto-completion and enable Vi editing mode"""
        readline.set_completer_delims(' \t\n=')
        readline.parse_and_bind("set editing-mode vi")

        try:
            """Prompt for user input"""
            question = input(f"{Color.BLUE}╭─ User \n╰─> {Color.ENDC}", end="")
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

    def to_markdown(text):
        text = text.replace('•', '  *')
        return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

    def run_subprocess(self, command):
        """Run a subprocess command"""
        try:
            subprocess.run(command, shell=True)
        except Exception as e:
            """error handling"""
            print(f"{Color.BRIGHTYELLOW}\n╰─> {Color.ENDC}{Color.BRIGHTRED}subprocess execution error: {e}{Color.ENDC}")

    def initialize_chat(self):
        """Initialize the chat session"""
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        instruction = GeminiChatConfig.chat_instruction(self.instruction_file)
        config = GeminiChatConfig.initialize_config()
        model = genai.GenerativeModel(
            generation_config=generation_config,
            model_name=self.model_name,
            safety_settings=safety_settings
        )
        """initiate chat model history"""
        chat = model.start_chat(history=[])
        return chat, instruction

    def generate_chat(self):
        """model generation response flow"""
        @staticmethod
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
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == GeminiChatConfig.HELP_COMMAND:
                    GeminiChatConfig.display_help()
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == GeminiChatConfig.RECONFIGURE_COMMAND:
                    config = GeminiChatConfig.reconfigure()
                    self.api_key = config['DEFAULT']['API']
                    self.loading_style = config['DEFAULT']['LoadingStyle']
                    self.instruction_file = config['DEFAULT']['InstructionFile']
                    self.model_name = config['DEFAULT']['ModelName']
                    GeminiChatConfig.initialize_genai_api(self.api_key)
                    chat, instruction = self.initialize_chat()
                    self.conversation_log = []
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == GeminiChatConfig.PRINT_COMMAND:
                    """Save conversation log to a JSON file"""
                    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    log_file_name = f"{GeminiChatConfig.LOG_FOLDER}/log_{current_datetime}.json"
                    with open(log_file_name, "w") as file:
                        json.dump(self.conversation_log, file, indent=4)
                    print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Conversation log saved to {log_file_name}{Color.ENDC}\n")
                    user_input = ""
                    multiline_mode = False
                    continue
                elif not user_input:
                    print(f'\n{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}Please enter your command/prompt{Color.ENDC}\n')
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input.startswith("run "):
                    """Run a subprocess command"""
                    command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}Executing User Command{Color.ENDC}')
                    self.run_subprocess(command)
                    user_input = ""
                    multiline_mode = False
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

                    """Log the conversation"""
                    self.conversation_log.append(f"User: {user_input}")
                    self.conversation_log.append(f"Model: {sanitized_response}")

                user_input = ""
                multiline_mode = False

        except KeyboardInterrupt:
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}")

        except Exception as e:
            """error handling"""
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.BRIGHTRED}An unexpected Error occurred: {e}{Color.ENDC}")
            stop_loading = True

if __name__ == "__main__":
    chat_app = GeminiChat()
    chat_app.generate_chat()
