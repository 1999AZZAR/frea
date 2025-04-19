import os
import sys
import configparser
import google.generativeai as genai
import subprocess
from color import Color


class ChatConfig:
    # Command constants
    EXIT_COMMAND = "exit"
    CLEAR_COMMAND = "clear"
    RESET_COMMAND = "reset"
    SAVE_COMMAND = "save"
    PRINT_COMMAND = "print"
    EXPORT_COMMAND = "export"
    MODEL_COMMAND = "model"
    SERVICE_COMMAND = "provider"
    RECONFIGURE_COMMAND = "recon"
    HELP_COMMAND = "help"

    # Configuration file paths
    CONFIG_FILE = "./config/config.ini"
    LOG_FOLDER = "logs"
    EXPORT_FOLDER = "exports"

    # Default settings
    DEFAULT_LOADING_STYLE = "L1"
    DEFAULT_INSTRUCTION_FILE = "./config/instruction.txt"
    DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"  # Default model for Gemini
    DEFAULT_GROQ_MODEL = "llama3-8b-8192"  # Default model for Groq
    DEFAULT_AI_SERVICE = "gemini"  # Default AI service

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
        """
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}No Configuration found. Creating new configuration file.{Color.ENDC}\n"
        )

        gemini_api = input("Enter the Gemini API key: ")
        groq_api = input("Enter the Groq API key: ")
        ai_service = input("Enter the AI service (gemini/groq): ").lower()
        if ai_service not in ["gemini", "groq"]:
            ChatConfig._exit_with_error(
                "Invalid AI service. Must be 'gemini' or 'groq'."
            )

        # Set the default model based on the selected AI service
        default_model = (
            ChatConfig.DEFAULT_GEMINI_MODEL
            if ai_service == "gemini"
            else ChatConfig.DEFAULT_GROQ_MODEL
        )

        config["DEFAULT"] = {
            "GeminiAPI": gemini_api,
            "GroqAPI": groq_api,
            "AIService": ai_service,
            "LoadingStyle": input(
                f"Enter the loading style (default: '{ChatConfig.DEFAULT_LOADING_STYLE}'): "
            )
            or ChatConfig.DEFAULT_LOADING_STYLE,
            "InstructionFile": input(
                f"Enter the instruction file path (default: '{ChatConfig.DEFAULT_INSTRUCTION_FILE}'): "
            )
            or ChatConfig.DEFAULT_INSTRUCTION_FILE,
            "AIModel": input(f"Enter the AI model name (default: '{default_model}'): ")
            or default_model,
        }

        with open(ChatConfig.CONFIG_FILE, "w") as configfile:
            config.write(configfile)

        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Configuration saved successfully!{Color.ENDC}\n"
        )

    @staticmethod
    def reconfigure():
        """
        Prompts the user to re-enter configuration settings and saves them.

        Returns:
            configparser.ConfigParser: The updated configuration.
        """
        config = configparser.ConfigParser()

        gemini_api = input("Enter the new Gemini API key: ")
        groq_api = input("Enter the new Groq API key: ")
        ai_service = input("Enter the AI service (gemini/groq): ").lower()
        if ai_service not in ["gemini", "groq"]:
            ChatConfig._exit_with_error(
                "Invalid AI service. Must be 'gemini' or 'groq'."
            )

        # Set the default model based on the selected AI service
        default_model = (
            ChatConfig.DEFAULT_GEMINI_MODEL
            if ai_service == "gemini"
            else ChatConfig.DEFAULT_GROQ_MODEL
        )

        config["DEFAULT"] = {
            "GeminiAPI": gemini_api,
            "GroqAPI": groq_api,
            "AIService": ai_service,
            "LoadingStyle": input(
                f"Enter the loading style (default: '{ChatConfig.DEFAULT_LOADING_STYLE}'): "
            )
            or ChatConfig.DEFAULT_LOADING_STYLE,
            "InstructionFile": input(
                f"Enter the instruction file path (default: '{ChatConfig.DEFAULT_INSTRUCTION_FILE}'): "
            )
            or ChatConfig.DEFAULT_INSTRUCTION_FILE,
            "AIModel": input(f"Enter the AI model name (default: '{default_model}'): ")
            or default_model,
        }

        # Save the updated config
        ChatConfig.save_config(config)

        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Configuration updated successfully!{Color.ENDC}\n"
        )
        return config

    @staticmethod
    def save_config(config):
        """
        Saves the current configuration to the config file.

        Args:
            config (configparser.ConfigParser): The configuration object to save.
        """
        with open(ChatConfig.CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Configuration saved successfully!{Color.ENDC}\n"
        )

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
    def generation_config():
        """
        Returns configuration settings for the language model.

        Returns:
            dict: The generation configuration.
        """
        return {
            "max_tokens": 2048,
            "temperature": 0.25,
            "top_p": 0.65,
            "top_k": 0.35,
            "frequency_penalty": 1.2,
        }

    @staticmethod
    def safety_settings():
        """
        Returns safety settings for the model.

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
{Color.RED}freak        Robotic      Entity with  Amusement{Color.ENDC}

{Color.BRIGHTCYAN}Available Commands:{Color.ENDC}

{Color.BRIGHTYELLOW}General:{Color.ENDC}
  {Color.BRIGHTGREEN}{ChatConfig.HELP_COMMAND}{Color.ENDC}      Show help menu
  {Color.BRIGHTGREEN}{ChatConfig.EXIT_COMMAND}{Color.ENDC}      Exit application
  {Color.BRIGHTGREEN}{ChatConfig.CLEAR_COMMAND}{Color.ENDC}     Clear screen
  {Color.BRIGHTGREEN}{ChatConfig.RESET_COMMAND}{Color.ENDC}     Reset chat session
  {Color.BRIGHTGREEN}{ChatConfig.SAVE_COMMAND}{Color.ENDC}      Save chat as JSON (exports/)
  {Color.BRIGHTGREEN}{ChatConfig.PRINT_COMMAND}{Color.ENDC}     Save chat as Markdown (exports/)
  {Color.BRIGHTGREEN}{ChatConfig.EXPORT_COMMAND}{Color.ENDC}    Export code blocks (exports/)
  {Color.BRIGHTGREEN}{ChatConfig.SERVICE_COMMAND}{Color.ENDC}   Switch AI provider
  {Color.BRIGHTGREEN}{ChatConfig.MODEL_COMMAND}{Color.ENDC}     Switch AI model
  {Color.BRIGHTGREEN}{ChatConfig.RECONFIGURE_COMMAND}{Color.ENDC}  Reconfigure settings

{Color.BRIGHTYELLOW}Shell Commands:{Color.ENDC}
  {Color.BRIGHTGREEN}run /<cmd>{Color.ENDC}     Execute shell command
  {Color.BRIGHTGREEN}send <file_path>{Color.ENDC}        Send file for review

{Color.BRIGHTYELLOW}AI Tools:{Color.ENDC}
  {Color.BRIGHTGREEN}wiki <query>{Color.ENDC}      Wikipedia summary
  {Color.BRIGHTGREEN}calc <expression>{Color.ENDC}  Calculate expression
  {Color.BRIGHTGREEN}vim <file_path>{Color.ENDC}  Open file in Vim

{Color.BRIGHTYELLOW}File Operations:{Color.ENDC}
  {Color.BRIGHTGREEN}ls [path]{Color.ENDC}          List directory contents
  {Color.BRIGHTGREEN}cat <file_path>{Color.ENDC}    Display file content
  {Color.BRIGHTGREEN}head <file_path> [N]{Color.ENDC}  Show first N lines
  {Color.BRIGHTGREEN}tail <file_path> [N]{Color.ENDC}  Show last N lines
  {Color.BRIGHTGREEN}grep <pattern> [path]{Color.ENDC}  Search regex in files
  {Color.BRIGHTGREEN}write <file_path> <content>{Color.ENDC}  Overwrite file
  {Color.BRIGHTGREEN}append <file_path> <content>{Color.ENDC}  Append to file
  {Color.BRIGHTGREEN}delete <file_path>{Color.ENDC}       Delete file
  {Color.BRIGHTGREEN}move <src> <dst>{Color.ENDC}         Move/rename file
  {Color.BRIGHTGREEN}copy <src> <dst>{Color.ENDC}         Copy file
"""
        print(f"\n{help_text}")
