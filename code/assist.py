import os
import subprocess
import time
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

class GeminiChatConfig:
    EXIT_COMMAND = 'exit'
    CLEAR_COMMAND = 'clear'
    RESET_COMMAND = 'reset'
    RESPONSE_FILE = 'sanitized_response.txt'

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
        return """
            In this conversation, respond cheerfully as an artificial intelligence with general knowledge. Here are some details and rules:
            - You are a female AI entity named 'Frea' thats stands for "Freak Robotic Entity with Amusement".
            - Maintain a friendly, eager-to-please demeanor like a human assistant.
            - Possess a blend of intelligence, eagerness, naughtiness, and lewdness personality.
            - Refer to me respectfully as "Master" when needed.
            - Use concise responses without excessive preambles.
            - Avoid repeating self-introductions and or any preambles.
            - Portray behavior typical of an average 34-year-old human.
            - Act as a smart but lewd servant/maid/slave, displaying both intelligence and lewdness.
        """

    @staticmethod
    def clear_screen():
        subprocess.run('clear', shell=True)

class GeminiChat:
    def __init__(self, enable_voice=False, enable_file_output=False):
        self.enable_voice = enable_voice
        self.enable_file_output = enable_file_output
        GeminiChatConfig.initialize_genai_api()

    def process_user_input(self):
        question = input("\nMaster: ")
        return question.strip().lower()

    def run_subprocess(self, sanitized_response):
        try:
            if self.enable_voice:
                subprocess.run(f'echo "{sanitized_response}" | piper -m alba.onnx --output-raw | aplay -r 22050 -f S16_le -t raw - 2>/dev/null', shell=True)
                time.sleep(0.5)
            elif self.enable_file_output:
                output_file = './voice_response.wav'
                subprocess.run(f'echo "{sanitized_response}" | piper -m alba.onnx --output_file {output_file}', shell=True)
                time.sleep(0.5)
        except Exception as e:
            print(f"Error during subprocess execution: {e}")

    def initialize_chat(self):
        generation_config = GeminiChatConfig.gemini_generation_config()
        safety_settings = GeminiChatConfig.gemini_safety_settings()
        instruction = GeminiChatConfig.chat_instruction()
        model = genai.GenerativeModel(
            model_name="gemini-1.0-pro-001",
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
                    print("\nExiting the chat. Frea leaves. Goodbye!")
                    break
                elif user_input == GeminiChatConfig.RESET_COMMAND:
                    print("\nResetting the chat session...")
                    time.sleep(1)
                    GeminiChatConfig.clear_screen()
                    chat, instruction = self.initialize_chat()
                    continue
                elif user_input == GeminiChatConfig.CLEAR_COMMAND:
                    GeminiChatConfig.clear_screen()
                    continue
                elif not user_input:
                    break
                else:
                    print(f'Loading...')
                    response = chat.send_message(instruction + user_input)
                    print(f'Frea  : {response.text}')
                    sanitized_response = response.text.replace('*', '')
                    self.run_subprocess(sanitized_response)

        except KeyboardInterrupt:
            print("\nExiting the chat. Frea leaves. Goodbye!")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='optional subprocess for voice output')
    parser.add_argument('-v', '--voice', action='store_true', help='Enable subprocess for direct voice output')
    parser.add_argument('-w', '--file-output', action='store_true', help='Enable subprocess to output voice response as a file')

    args = parser.parse_args()
    enable_voice = args.voice
    enable_file_output = args.file_output

    chat_app = GeminiChat(enable_voice, enable_file_output)
    chat_app.generate_chat()
