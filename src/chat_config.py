import os
import sys
import configparser
import google.generativeai as genai
import subprocess
from color import Color

class ChatConfig:
    """Special commands and configuration for chat"""
    EXIT_COMMAND        = 'exit'
    CLEAR_COMMAND       = 'clear'
    RESET_COMMAND       = 'reset'
    PRINT_COMMAND       = 'print'
    MODEL_COMMAND       = 'model'
    RECONFIGURE_COMMAND = 'reconfigure'
    HELP_COMMAND        = 'help'
    CONFIG_FILE         = './config/config.ini'
    LOG_FOLDER          = 'logs'

    DEFAULT_LOADING_STYLE = 'L1'
    DEFAULT_INSTRUCTION_FILE = './config/instruction.txt'
    DEFAULT_GEMINI_MODEL = 'models/gemini-1.5-pro'
    DEFAULT_AI_SERVICE = 'gemini'

    @staticmethod
    def initialize_config():
        """Initialize the config.ini file"""
        config = configparser.ConfigParser()
        if not os.path.exists(ChatConfig.CONFIG_FILE):
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}No Configuration found Creating configuration file.{Color.ENDC}\n")
            gemini_api = input("Enter the Gemini API key: ")

            if not gemini_api:
                print(f"{Color.BRIGHTRED}Error: Gemini API key is required.{Color.ENDC}")
                sys.exit(1)

            config['DEFAULT'] = {
                'GeminiAPI': gemini_api,
                'AIService': ChatConfig.DEFAULT_AI_SERVICE,
                'LoadingStyle': input(f"Enter the loading style (e.g., L2, random, or press Enter for default'{ChatConfig.DEFAULT_LOADING_STYLE}'): ") or ChatConfig.DEFAULT_LOADING_STYLE,
                'InstructionFile': input(f"Enter the path to the instruction file (or press Enter for default'{ChatConfig.DEFAULT_INSTRUCTION_FILE}'): ") or ChatConfig.DEFAULT_INSTRUCTION_FILE,
                'GeminiModel': input(f"Enter the Gemini model name (or press Enter for default'{ChatConfig.DEFAULT_GEMINI_MODEL}'): ") or ChatConfig.DEFAULT_GEMINI_MODEL,
            }
            with open(ChatConfig.CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Configuration saved successfully!{Color.ENDC}\n")
        else:
            config.read(ChatConfig.CONFIG_FILE)
        return config

    @staticmethod
    def reconfigure():
        """Reconfigure the settings"""
        config = configparser.ConfigParser()
        gemini_api = input("Enter the New Gemini API key: ")

        if not gemini_api:
            print(f"{Color.BRIGHTRED}Error: Gemini API key is required.{Color.ENDC}")
            sys.exit(1)

        config['DEFAULT'] = {
            'GeminiAPI': gemini_api,
            'AIService': ChatConfig.DEFAULT_AI_SERVICE,
            'LoadingStyle': input(f"Enter the loading style (e.g., L1, random, or press Enter for default'{ChatConfig.DEFAULT_LOADING_STYLE}'): ") or ChatConfig.DEFAULT_LOADING_STYLE,
            'InstructionFile': input(f"Enter the path to the instruction file (or press Enter for default'{ChatConfig.DEFAULT_INSTRUCTION_FILE}'): ") or ChatConfig.DEFAULT_INSTRUCTION_FILE,
            'GeminiModel': input(f"Enter the Gemini model name (or press Enter for default'{ChatConfig.DEFAULT_GEMINI_MODEL}'): ") or ChatConfig.DEFAULT_GEMINI_MODEL,
        }
        with open(ChatConfig.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Configuration updated successfully!{Color.ENDC}\n")
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
    {Color.RED}freak        Robotic      Entity with  Amusement{Color.ENDC}\n
    {Color.BRIGHTCYAN}Command List:{Color.ENDC}
    {Color.BRIGHTGREEN}{ChatConfig.HELP_COMMAND}{Color.ENDC}  - Display this help information. Provides a list of all available commands and their descriptions.
    {Color.BRIGHTGREEN}{ChatConfig.EXIT_COMMAND}{Color.ENDC}  - Exit the application. Terminates the chat session and closes the application.
    {Color.BRIGHTGREEN}{ChatConfig.CLEAR_COMMAND}{Color.ENDC} - Clear the terminal screen. Clears all text from the terminal screen.
    {Color.BRIGHTGREEN}{ChatConfig.RESET_COMMAND}{Color.ENDC} - Reset the chat session. Clears the chat history and restarts the chat session.
    {Color.BRIGHTGREEN}{ChatConfig.PRINT_COMMAND}{Color.ENDC} - Saves to current chat session to a log file in JSON format.
    {Color.BRIGHTGREEN}{ChatConfig.MODEL_COMMAND}{Color.ENDC} - Change the AI model.
            Allows you to switch between different Gemini models.
    {Color.BRIGHTGREEN}{ChatConfig.RECONFIGURE_COMMAND}{Color.ENDC}    - Reconfigure the settings.
            Prompts you to re-enter configuration settings such as API keys and model preferences.
    {Color.BRIGHTGREEN}run (command){Color.ENDC}  - Run a subprocess command.
            Executes a shell command in the terminal (e.g., run ls).
    {Color.BRIGHTGREEN}(prompt) -wiki{Color.ENDC} - Get additional info from Wikipedia to enhance the model's knowledge base.
            The system will search for:
            1. Up to three phrases enclosed in double quotes (e.g., "Python" "machine learning" "data science" -wiki).
            2. If no quotes are found, it will use the last two words of the prompt.
            For example:
                - "artificial intelligence" "neural networks" -wiki
                - Tell me about "quantum computing" and its applications -wiki
                - airplane -wiki
        """
        print(f"\n{help_text}")

    @staticmethod
    def initialize_apis(gemini_api_key):
        """Initialize the API keys"""
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        else:
            raise ValueError("Gemini API key is required")

    @staticmethod
    def gemini_generation_config():
        """Configuration for the Gemini language model"""
        return {
            'max_output_tokens': 1024,
            'temperature': 0.75,
            'candidate_count': 1,
            'top_k': 35,
            'top_p': 0.65,
            'stop_sequences': []
        }

    @staticmethod
    def gemini_safety_settings():
        """Safety settings for the Gemini model"""
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
            return "You are frea (freak robotic entity with amusement), a helpful assistant."

    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        subprocess.run('clear', shell=True)
