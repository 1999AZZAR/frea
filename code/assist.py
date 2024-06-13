import os, subprocess, time, re, readline, termios, tty, sys, threading
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
    # Path to the model instruction
    INSTRUCTION_FILE    = './instructions/general.txt'

    @staticmethod
    def initialize_genai_api():
        """Load API key from environment variable"""
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
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
    def chat_instruction():
        """Read the instruction file"""
        with open(GeminiChatConfig.INSTRUCTION_FILE, 'r') as file:
            return file.read()

    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        subprocess.run('clear', shell=True)

class GeminiChat:
    def __init__(self):
        GeminiChatConfig.initialize_genai_api()
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

    def initialize_chat(self):
        """Initialize the chat session"""
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        instruction = GeminiChatConfig.chat_instruction()
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
        def loading_indicator():
            """loading indicator animation"""
            cursor_hide()
            while not stop_loading:
                loading = [' ∙∙∙∙∙ ', ' ●∙∙∙∙ ', ' ∙●∙∙∙ ', ' ∙∙●∙∙ ', ' ∙∙∙●∙ ', ' ∙∙∙∙● ']
                for frame in loading:
                    print(f"{Color.LIGHTPURPLE}\r{frame}Processing{Color.ENDC}", end="")
                    time.sleep(0.15)
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
                elif user_input == GeminiChatConfig.PRINT_COMMAND:
                    """Save conversation log to a file"""
                    with open("conversation_log.txt", "w") as file:
                        for line in self.conversation_log:
                            file.write(line + "\n")
                    print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.PASTELPINK}Conversation log saved to conversation_log.txt{Color.ENDC}\n")
                    continue
                elif not user_input:
                    break
                elif user_input.startswith("run "):
                    """Run a subprocess command"""
                    command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}executing user command{Color.ENDC}')
                    self.run_subprocess(command)
                    print(f'\n')
                else:
                    """Send user input to the language model and print the response"""
                    stop_loading = False
                    loading_thread = threading.Thread(target=loading_indicator)
                    loading_thread.start()

                    response = chat.send_message(instruction + user_input)

                    stop_loading = True
                    loading_thread.join()

                    sanitized_response = self.remove_emojis(response.text)
                    sanitized_response = sanitized_response.replace('*', '')
                    print(f'{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{sanitized_response}')

                    """Log the conversation"""
                    self.conversation_log.append(f"User: {user_input}")
                    self.conversation_log.append(f"Frea: {sanitized_response}")

                user_input = ""

        except KeyboardInterrupt:
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}")

        except Exception as e:
            """error handling"""
            print(f"{Color.BRIGHTYELLOW}\n╭─ Frea \n╰─> {Color.ENDC}{Color.BRIGHTRED}An unexpected error occurred: {e}{Color.ENDC}")
            stop_loading = True

if __name__ == "__main__":
    chat_app = GeminiChat()
    chat_app.generate_chat()
