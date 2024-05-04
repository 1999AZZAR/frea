import os
import subprocess
import time
import argparse
import re
from dotenv import load_dotenv
import google.generativeai as genai

class Color:
    HEADER = '\033[95m'       # Light purple
    OKBLUE = '\033[94m'       # Light blue
    OKCYAN = '\033[96m'       # Light cyan
    OKGREEN = '\033[92m'      # Light green
    WARNING = '\033[93m'      # Yellow
    RED = '\033[91m'          # Light red
    ENDC = '\033[0m'          # End of color
    BOLD = '\033[1m'          # Bold
    UNDERLINE = '\033[4m'     # Underline
    YELLOWIST = '\033[97m'    # Yellowish white

class GeminiChatConfig:
    EXIT_COMMAND = 'exit'
    CLEAR_COMMAND = 'clear'
    RESET_COMMAND = 'reset'
    RESPONSE_FILE = 'sanitized_response.txt'
    INSTRUCTION_FILE = './instructions/freya.txt'

    @staticmethod
    def initialize_genai_api():
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)

    @staticmethod
    def gemini_generation_config():
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
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]

    @staticmethod
    def chat_instruction():
        with open(GeminiChatConfig.INSTRUCTION_FILE, 'r') as file:
            return file.read()

    @staticmethod
    def clear_screen():
        subprocess.run('clear', shell=True)

class GeminiChat:
    def __init__(self, enable_voice=False, enable_file_output=False):
        self.enable_voice = enable_voice
        self.enable_file_output = enable_file_output
        GeminiChatConfig.initialize_genai_api()

    def process_user_input(self):
        question = input(f"{Color.OKCYAN}╭─ Master \n╰─> {Color.ENDC}")
        return question.strip().lower()

    def remove_emojis(self, text):
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
        try:
            subprocess.run(command, shell=True)
        except Exception as e:
            print(f"{Color.RED}Error during subprocess execution: {e}{Color.ENDC}")

    def initialize_chat(self):
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
        try:
            chat, instruction = self.initialize_chat()

            while True:
                user_input = self.process_user_input()

                if user_input == GeminiChatConfig.EXIT_COMMAND:
                    print(f"\n{Color.WARNING}Exiting the chat. freya leaves. Goodbye!{Color.ENDC}")
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
                    command = user_input[4:].strip()
                    print(f'{Color.OKGREEN}\n╭─ freya \n╰─> {Color.ENDC}{Color.RED}executing user command{Color.ENDC}')
                    self.run_subprocess(command)
                    print(f'\n')
                else:
                    response = chat.send_message(instruction + user_input)
                    sanitized_response = self.remove_emojis(response.text)
                    sanitized_response = sanitized_response.replace('*', '')
                    print(f'{Color.OKGREEN}\n╭─ freya \n╰─> {Color.ENDC}{Color.YELLOWIST}{sanitized_response}{Color.ENDC}')

        except KeyboardInterrupt:
            print(f"\n{Color.WARNING}Exiting the chat. freya leaves. Goodbye!{Color.ENDC}")

        except Exception as e:
            print(f"{Color.RED}An unexpected error occurred: {e}{Color.ENDC}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='optional subprocess for voice output')
    parser.add_argument('-v', '--voice', action='store_true', help='Enable subprocess for direct voice output')
    parser.add_argument('-w', '--file-output', action='store_true', help='Enable subprocess to output voice response as a file')

    args = parser.parse_args()
    enable_voice = args.voice
    enable_file_output = args.file_output

    chat_app = GeminiChat(enable_voice, enable_file_output)
    chat_app.generate_chat()
