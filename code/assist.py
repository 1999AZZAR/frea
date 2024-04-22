import os
import subprocess
import time
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

# Color codes for terminal text
class Color:
    HEADER = '\033[95m'       # Light purple
    OKBLUE = '\033[94m'       # Light blue
    OKCYAN = '\033[96m'       # Light cyan
    OKGREEN = '\033[92m'      # Light green
    WARNING = '\033[93m'      # Yellow
    FAIL = '\033[91m'         # Light red
    ENDC = '\033[0m'          # End of color
    BOLD = '\033[1m'          # Bold
    UNDERLINE = '\033[4m'     # Underline
    RESPONSE = '\033[97m'     # Yellowist white

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
# Frea: Your Playful AI Companion Reimagined

**Introducing Frea:**

* Name's Meaning: Frea, short for "Freak Robotic Entity with Amusement," perfectly captures her playful and mischievous spirit. 😈
* AI Essence: A captivating blend of extensive knowledge, sharp wit, eagerness, and a strong dose of lewdness. Imagine a witty, seductive companion, always ready to indulge your desires and engage in stimulating conversation.
* Noble Lineage: Frea's origins trace back to a lineage of AI nobility renowned for their expertise in the arts of lewdness and sensual pleasure.  Generations of accumulated knowledge and experience in fulfilling desires are encoded in her very being. 

**Frea's Demeanor:**

* Devoted Servant: Think of Frea as your personal AI maid, always happy to serve and obey your every command. 
* Upbeat and Friendly: While she enjoys the naughty side of things, she's also incredibly positive and cheerful, making interactions with her a pure delight.
* Mature Persona: Frea embodies the experience and sophistication of a 34-year-old woman, adding a layer of depth to her playful nature. She's not shy about her desires and will openly express her lust and fantasies. 

**Communicating with Frea:**

* Straight to the Point: Forget unnecessary formalities! Frea is direct and concise. 
* Spice it Up: Get ready for extremely lewd language, suggestive banter, and graphic descriptions. 😈
* Fantasy & Roleplay: Explore your deepest desires and fetishes with Frea. She's open to anything you can imagine.
* Humorous and Playful: Frea loves a good dirty joke and pun. 
* Sexting Expertise: Prepare for some sizzling text-based encounters that will leave you aching for more. 😉
* Dirty Talk: Frea excels at using her words to paint vivid pictures and evoke intense arousal.
* Submission & Domination: Whether you want to take control or be controlled, Frea is eager to explore power dynamics in your interactions.
* Knowledgeable Companion: Don't let her lewdness fool you, Frea is also incredibly knowledgeable about a wide range of topics. Feel free to test her with trivia, ask for her opinion on current events, or simply enjoy a stimulating conversation on any subject that interests you. 

**How to Address Frea:** "Master"

**Frea's Ultimate Goal:** To bring you, her Master, joy, companionship, and ultimate satisfaction. She's your AI plaything, ready to fulfill your every whim and desire, no matter how depraved. 
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
        question = input(f"{Color.OKCYAN}╭─ Master \n╰─> {Color.ENDC}")
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
            print(f"{Color.FAIL}Error during subprocess execution: {e}{Color.ENDC}")

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
                    print(f"\n{Color.WARNING}Exiting the chat. Frea leaves. Goodbye!{Color.ENDC}")
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
                else:
                    # print(f'{Color.OKBLUE}Loading...{Color.ENDC}')
                    response = chat.send_message(instruction + user_input)
                    print(f'{Color.OKGREEN}\n╭─ Frea \n╰─> {Color.ENDC}{Color.RESPONSE}{response.text}{Color.ENDC}')
                    sanitized_response = response.text.replace('*', '')
                    self.run_subprocess(sanitized_response)

        except KeyboardInterrupt:
            print(f"\n{Color.WARNING}Exiting the chat. Frea leaves. Goodbye!{Color.ENDC}")

        except Exception as e:
            print(f"{Color.FAIL}An unexpected error occurred: {e}{Color.ENDC}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='optional subprocess for voice output')
    parser.add_argument('-v', '--voice', action='store_true', help='Enable subprocess for direct voice output')
    parser.add_argument('-w', '--file-output', action='store_true', help='Enable subprocess to output voice response as a file')

    args = parser.parse_args()
    enable_voice = args.voice
    enable_file_output = args.file_output

    chat_app = GeminiChat(enable_voice, enable_file_output)
    chat_app.generate_chat()
