import os
import sys
import configparser
import google.generativeai as genai
import subprocess
from color import Color


class ChatConfig:
    """
    Manages chat commands and configurations.
    """

    # Command constants
    EXIT_COMMAND = "exit"
    CLEAR_COMMAND = "clear"
    RESET_COMMAND = "reset"
    SAVE_COMMAND = "save"
    PRINT_COMMAND = "print"
    MODEL_COMMAND = "model"
    RECONFIGURE_COMMAND = "recon"
    HELP_COMMAND = "help"

    # Configuration file paths
    CONFIG_FILE = "./config/config.ini"
    LOG_FOLDER = "logs"

    # Default settings
    DEFAULT_LOADING_STYLE = "L1"
    DEFAULT_INSTRUCTION_FILE = "./config/instruction.txt"
    DEFAULT_GEMINI_MODEL = "models/gemini-1.5-pro"
    DEFAULT_AI_SERVICE = "gemini"

    @staticmethod
    def initialize_config():
        """
        Initializes the configuration file, prompting user input if necessary.

        Returns:
            configparser.ConfigParser: The loaded configuration.
        """
        config = configparser.ConfigParser()

        if not os.path.exists(ChatConfig.CONFIG_FILE):
            ChatConfig._create_new_config(config)
        else:
            config.read(ChatConfig.CONFIG_FILE)

        return config

    @staticmethod
    def _create_new_config(config):
        """
        Handles creation of a new configuration file.

        Args:
            config (configparser.ConfigParser): The configuration object to populate.
        """
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}No Configuration found. Creating new configuration file.{Color.ENDC}\n"
        )

        gemini_api = input("Enter the Gemini API key: ")
        if not gemini_api:
            ChatConfig._exit_with_error("Gemini API key is required.")

        config["DEFAULT"] = {
            "GeminiAPI": gemini_api,
            "AIService": ChatConfig.DEFAULT_AI_SERVICE,
            "LoadingStyle": input(
                f"Enter the loading style (default: '{ChatConfig.DEFAULT_LOADING_STYLE}'): "
            )
            or ChatConfig.DEFAULT_LOADING_STYLE,
            "InstructionFile": input(
                f"Enter the instruction file path (default: '{ChatConfig.DEFAULT_INSTRUCTION_FILE}'): "
            )
            or ChatConfig.DEFAULT_INSTRUCTION_FILE,
            "GeminiModel": input(
                f"Enter the Gemini model name (default: '{ChatConfig.DEFAULT_GEMINI_MODEL}'): "
            )
            or ChatConfig.DEFAULT_GEMINI_MODEL,
        }

        with open(ChatConfig.CONFIG_FILE, "w") as configfile:
            config.write(configfile)

        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Configuration saved successfully!{Color.ENDC}\n"
        )

    @staticmethod
    def reconfigure():
        """
        Prompts the user to re-enter configuration settings.

        Returns:
            configparser.ConfigParser: The updated configuration.
        """
        config = configparser.ConfigParser()

        gemini_api = input("Enter the new Gemini API key: ")
        if not gemini_api:
            ChatConfig._exit_with_error("Gemini API key is required.")

        config["DEFAULT"] = {
            "GeminiAPI": gemini_api,
            "AIService": ChatConfig.DEFAULT_AI_SERVICE,
            "LoadingStyle": input(
                f"Enter the loading style (default: '{ChatConfig.DEFAULT_LOADING_STYLE}'): "
            )
            or ChatConfig.DEFAULT_LOADING_STYLE,
            "InstructionFile": input(
                f"Enter the instruction file path (default: '{ChatConfig.DEFAULT_INSTRUCTION_FILE}'): "
            )
            or ChatConfig.DEFAULT_INSTRUCTION_FILE,
            "GeminiModel": input(
                f"Enter the Gemini model name (default: '{ChatConfig.DEFAULT_GEMINI_MODEL}'): "
            )
            or ChatConfig.DEFAULT_GEMINI_MODEL,
        }

        with open(ChatConfig.CONFIG_FILE, "w") as configfile:
            config.write(configfile)

        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Configuration updated successfully!{Color.ENDC}\n"
        )
        return config

    @staticmethod
    def display_help():
        """
        Displays help information with a list of available commands.
        """
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
    {Color.BRIGHTGREEN}{ChatConfig.SAVE_COMMAND}{Color.ENDC}  - Saves the current chat history to a file in JSON format.
    {Color.BRIGHTGREEN}{ChatConfig.PRINT_COMMAND}{Color.ENDC} - Saves the current chat history to a file in Markdown format.
    {Color.BRIGHTGREEN}{ChatConfig.MODEL_COMMAND}{Color.ENDC} - Change the AI model.
            Allows you to switch between different Gemini models.
    {Color.BRIGHTGREEN}{ChatConfig.RECONFIGURE_COMMAND}{Color.ENDC} - Reconfigure the settings.
            Prompts you to re-enter configuration settings such as API keys and model preferences.
    {Color.BRIGHTGREEN}run  {Color.ENDC} - Run a subprocess command.
    {Color.BRIGHTGREEN}'/'  {Color.ENDC} - same as run.
            Executes a shell command in the terminal (e.g., run ls or /ls).
    {Color.BRIGHTGREEN}-wiki{Color.ENDC} - Get additional info from Wikipedia to enhance the model's knowledge base.
            The system will search for:
            1. Up to three phrases enclosed in double quotes (e.g., "Python" "machine learning" "data science" -wiki).
            2. If text is enclosed in backticks (e.g., `Python`), it will be treated as a Wikipedia query.
            3. If no quotes or backticks are found, it will use the last two words of the prompt.
            For example:
                - "artificial intelligence" "neural networks" -wiki
                - Tell me about `quantum computing` and its applications
                - airplane -wiki
        """
        print(f"\n{help_text}")

    @staticmethod
    def initialize_apis(gemini_api_key):
        """
        Configures the Gemini API key.

        Args:
            gemini_api_key (str): The Gemini API key.
        """
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        else:
            ChatConfig._exit_with_error("Gemini API key is required.")

    @staticmethod
    def gemini_generation_config():
        """
        Returns configuration settings for the Gemini language model.

        Returns:
            dict: The generation configuration.
        """
        return {
            "max_output_tokens": 1024,
            "temperature": 0.25,
            "candidate_count": 1,
            "top_k": 35,
            "top_p": 0.65,
            "stop_sequences": [],
        }

    @staticmethod
    def gemini_safety_settings():
        """
        Returns safety settings for the Gemini model.

        Returns:
            list: The safety settings.
        """
        return [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

    @staticmethod
    def chat_instruction(instruction_file):
        """
        Loads chat instructions from a file or falls back to default.

        Args:
            instruction_file (str): The path to the instruction file.

        Returns:
            str: The chat instructions.
        """
        if os.path.exists(instruction_file):
            with open(instruction_file, "r") as file:
                return file.read()
        else:
            print(
                f"{Color.BRIGHTRED}Instruction file not found. Using fallback instructions.{Color.ENDC}"
            )
            return "You are frea (freak robotic entity with amusement), a helpful assistant."

    @staticmethod
    def clear_screen():
        """
        Clears the terminal screen.
        """
        subprocess.run("clear", shell=True)

    @staticmethod
    def _exit_with_error(message):
        """
        Prints an error message and exits the program.

        Args:
            message (str): The error message to display.
        """
        print(f"{Color.BRIGHTRED}Error: {message}{Color.ENDC}")
        sys.exit(1)
