import os
import subprocess
import time
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

class GeminiChatConfig:
    EXIT_COMMAND = 'exit'
    CLEAR_COMMAND = 'clear'
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
            - You are a female AI entity named Frea.
            - Maintain a friendly, eager-to-please demeanor like a human assistant.
            - Possess a blend of intelligence, eagerness, naughtiness, and lewdness personality.
            - Refer to me respectfully as "Master" when needed.
            - Avoid repeating self-introductions.
            - Use concise responses without excessive preambles.
            - Portray behavior typical of an average 34-year-old human.
            - Act as a smart but lewd servant/maid/slave, displaying both intelligence and lewdness.
        """

    @staticmethod
    def clear_screen():
        subprocess.run('clear', shell=True)


class GeminiChat:
    def __init__(self, enable_subprocess=False):
        self.enable_subprocess = enable_subprocess
        GeminiChatConfig.initialize_genai_api()

    def process_user_input(self):
        question = input("\nMaster: ")
        return question.strip().lower()

    def run_subprocess(self, sanitized_response):
        try:
            if self.enable_subprocess:
                with open(GeminiChatConfig.RESPONSE_FILE, 'w') as file:
                    file.write(sanitized_response)
                subprocess.Popen(f'cat {GeminiChatConfig.RESPONSE_FILE} | piper -m alba.onnx --output-raw | aplay -r 22050 -f S16_le -t raw - 2>/dev/null', shell=True)
                time.sleep(1)
        except Exception as e:
            print(f"Error during subprocess execution: {e}")

    def generate_chat(self):
        try:
            generation_config = GeminiChatConfig.gemini_generation_config()
            safety_settings = GeminiChatConfig.gemini_safety_settings()
            instruction = GeminiChatConfig.chat_instruction()
            model = genai.GenerativeModel(
                model_name="gemini-1.0-pro-001",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=[])

            while True:
                user_input = self.process_user_input()

                if user_input == GeminiChatConfig.EXIT_COMMAND:
                    print("\nExiting the chat. Frea leaves. Goodbye!")
                    break
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
    parser = argparse.ArgumentParser(description='Gemini Chat with optional subprocess for voice output')
    parser.add_argument('-v', '--voice', action='store_true', help='Enable subprocess for voice output')

    args = parser.parse_args()
    enable_subprocess = args.voice

    chat_app = GeminiChat(enable_subprocess)
    chat_app.generate_chat()
