import os
import subprocess
import time
import re
import readline  # Module for enabling terminal history and navigation

from dotenv import load_dotenv
import google.generativeai as genai
import threading  # Module for creating loading indicator

class Color:
    # ANSI escape codes for terminal colors
    OKBLUE      = '\033[94m' # Light blue
    OKCYAN      = '\033[96m' # Light cyan
    OKGREEN     = '\033[92m' # Light green
    WARNING     = '\033[93m' # Yellow
    RED         = '\033[91m' # Light red
    ENDC        = '\033[0m'  # End of color
    YELLOWIST   = '\033[97m' # Yellowish white
    PURPLE      = '\033[35m' # Purple

class GeminiChatConfig:
    # Special commands for chat
    EXIT_COMMAND        = 'exit'
    CLEAR_COMMAND       = 'clear'
    RESET_COMMAND       = 'reset'
    INSTRUCTION_FILE    = './instructions/general.txt'  # Path to the instruction file

    @staticmethod
    def initialize_genai_api():
        # Load API key from environment variable
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)

    @staticmethod
    def gemini_generation_config():
        # Configuration for the Gemini language model
        return {
            'max_output_tokens': 2000,
            'temperature': 0.90,
            'candidate_count': 1,
            'top_k': 35,
            'top_p': 0.65,
            'stop_sequences': []
        }

    @staticmethod
    def gemini_safety_settings():
        # Safety settings for the Gemini language model
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

    @staticmethod
    def chat_instruction():
        # Read the instruction file for the chat
        with open(GeminiChatConfig.INSTRUCTION_FILE, 'r') as file:
            return file.read()

    @staticmethod
    def clear_screen():
        # Clear the terminal screen
        subprocess.run('clear', shell=True)

class GeminiChat:
    def __init__(self):
        GeminiChatConfig.initialize_genai_api()
        readline.parse_and_bind("tab: complete")  # Bind the tab key for auto-completion

    def process_user_input(self):
        # Set delimiters for auto-completion and enable Vi editing mode
        readline.set_completer_delims(' \t\n=')
        readline.parse_and_bind("set editing-mode vi")

        try:
            # Prompt for user input with colored prefix
            question = input(f"{Color.OKCYAN}╭─ User \n╰─> {Color.ENDC}")
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt")
            return ""
        return question.strip().lower()

    def remove_emojis(self, text):
        # Remove emojis from the input text
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
        # Run a subprocess command
        try:
            subprocess.run(command, shell=True)
        except Exception as e:
            print(f"{Color.RED}Error during subprocess execution: {e}{Color.ENDC}")

    def initialize_chat(self):
        # Initialize the chat session with the Gemini language model
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        instruction = GeminiChatConfig.chat_instruction()
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro-latest",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        chat = model.start_chat(history=[])
        return chat, instruction

    def generate_chat(self):
        def loading_indicator():
            while not stop_loading:
                for char in "|/-\\":
                    print(f"{Color.PURPLE}\rProceeding... {char}{Color.ENDC}", end="")
                    time.sleep(0.1)
        
        try:
            chat, instruction = self.initialize_chat()

            while True:
                user_input = self.process_user_input()

                # Handle special commands
                if user_input == GeminiChatConfig.EXIT_COMMAND:
                    print(f"\n{Color.WARNING}Exiting the chat. Goodbye!{Color.ENDC}")
                    break
                elif user_input == GeminiChatConfig.RESET_COMMAND:
                    print(f"\n{Color.WARNING}Resetting the chat session...{Color.ENDC}")
                    time.sleep(1)
                    GeminiChatConfig.clear_screen()
                    chat, instruction = self.initialize_chat()
                    continue
                elif user_input == GeminiChatConfig.CLEAR_COMMAND:
                    GeminiChatConfig.clear_screen()
                    continue
                elif not user_input:
                    break
                elif user_input.startswith("run "):
                    # Run a subprocess command
                    command = user_input[4:].strip()
                    print(f'{Color.OKGREEN}\n╭─ Model \n╰─> {Color.ENDC}{Color.RED}executing user command{Color.ENDC}')
                    self.run_subprocess(command)
                    print(f'\n')
                else:
                    # Send user input to the language model and print the response
                    stop_loading = False
                    loading_thread = threading.Thread(target=loading_indicator)
                    loading_thread.start()

                    response = chat.send_message(instruction + user_input)
                    
                    stop_loading = True
                    loading_thread.join()
                    print("\r" + " " * 20 + "\r", end="")  # Clear the loading indicator line
                    
                    sanitized_response = self.remove_emojis(response.text)
                    sanitized_response = sanitized_response.replace('*', '')
                    print(f'{Color.OKGREEN}\n╭─ Model \n╰─> {Color.ENDC}{Color.YELLOWIST}{sanitized_response}{Color.ENDC}')

        except KeyboardInterrupt:
            print(f"\n{Color.WARNING}Exiting the chat. Goodbye!{Color.ENDC}")

        except Exception as e:
            print(f"{Color.RED}An unexpected error occurred: {e}{Color.ENDC}")

if __name__ == "__main__":
    chat_app = GeminiChat()
    chat_app.generate_chat()
