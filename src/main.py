import sys
import threading
import logging
import time
import re
from logging.handlers import RotatingFileHandler
from color import Color
from chat_initializer import ChatInitializer
from chat_config import ChatConfig
from utils import (
    remove_emojis,
    run_subprocess,
    loading_animation,
    set_stop_loading,
    cursor_hide,
    cursor_show,
)
import google.generativeai as genai
import configparser
from printer import save_log, print_log
import atexit

# Configure logging with RotatingFileHandler
log_handler = RotatingFileHandler(
    "./logs/error.log", maxBytes=0.5 * 1024 * 1024, backupCount=3
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)


class AIChat:
    def __init__(self):
        """
        Initializes the AIChat application by loading configuration and setting up the chat session.
        """
        self.initializer = ChatInitializer()
        self.gemini_api_key = self.initializer.gemini_api_key or ""
        self.ai_service = self._determine_ai_service()
        self.gemini_model = self.initializer.gemini_model
        self.chat_history = []
        self.loading_style = self.initializer.loading_style
        self.instruction = self.initializer.instruction

        # Register cleanup function to handle gRPC shutdown
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        Cleans up resources (e.g., gRPC connections) when the application exits.
        """
        if hasattr(genai, "_grpc_channel"):
            genai._grpc_channel.close()
            logging.info("gRPC channel closed.")

    def generate_chat(self):
        """
        Main chat generation loop. Handles user input, processes commands, and interacts with the AI model.
        """
        chat = self.initialize_chat()
        if chat is None:
            print(f"{Color.BRIGHTRED}Failed to initialize chat. Exiting...{Color.ENDC}")
            return

        user_input = ""
        multiline_mode = False

        while True:
            try:
                # Multiline input handling
                if multiline_mode:
                    print(f"{Color.BLUE}╰─❯❯ {Color.ENDC}", end="")
                else:
                    print(f"\n{Color.BLUE}╭─ master \n╰─❯❯ {Color.ENDC}", end="")

                user_input_line = input()

                if user_input_line.endswith("\\"):
                    user_input += user_input_line.rstrip("\\") + "\n"
                    multiline_mode = True
                    continue
                else:
                    user_input += user_input_line

                # Handle special commands (e.g., exit, reset, clear, etc.)
                if self.handle_special_commands(user_input):
                    user_input = ""
                    multiline_mode = False
                    continue

                # Handle empty input
                if not user_input:
                    print(
                        f"\n{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.LIGHTRED}Please enter your command/prompt{Color.ENDC}"
                    )
                    user_input = ""
                    multiline_mode = False
                    continue

                # Handle subprocess commands (e.g., run ls or /ls)
                if user_input.strip().lower().startswith(
                    "run "
                ) or user_input.strip().startswith("/"):
                    command = (
                        user_input[1:].strip()
                        if user_input.strip().startswith("/")
                        else user_input[4:].strip()
                    )
                    print(
                        f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea ─────────────────────────╮\n╰─❯❯ {Color.ENDC}{Color.LIGHTRED}Executing master Command{Color.ENDC}{Color.BRIGHTYELLOW} ❮❮─╯{Color.ENDC}"
                    )
                    run_subprocess(command)
                    user_input = ""
                    multiline_mode = False
                else:
                    # Process user input and get AI response
                    self.process_user_input(chat, user_input)
                    user_input = ""
                    multiline_mode = False

            except KeyboardInterrupt:
                print("\nKeyboard Interrupt")
                break
            except Exception as e:
                set_stop_loading(True)
                logging.error(f"Error during chat generation: {e}", exc_info=True)
                print(
                    f"\n{Color.BRIGHTRED}An error occurred. Please check the logs for more details.{Color.ENDC}"
                )
                break

    def handle_special_commands(self, user_input):
        """
        Handles special commands like exit, reset, clear, etc.

        Args:
            user_input (str): The user input to process.

        Returns:
            bool: True if a special command was handled, False otherwise.
        """
        command = user_input.strip().lower()
        if command == ChatConfig.EXIT_COMMAND:
            self._handle_exit_command()
        elif command == ChatConfig.RESET_COMMAND:
            self._handle_reset_command()
        elif command == ChatConfig.CLEAR_COMMAND:
            self._handle_clear_command()
        elif command == ChatConfig.HELP_COMMAND:
            self._handle_help_command()
        elif command == ChatConfig.RECONFIGURE_COMMAND:
            self._handle_reconfigure_command()
        elif command == ChatConfig.SAVE_COMMAND:
            self._handle_save_command()
        elif command == ChatConfig.PRINT_COMMAND:
            self._handle_print_command()
        elif command == ChatConfig.MODEL_COMMAND:
            self._handle_model_command()
        else:
            return False
        return True

    def _handle_exit_command(self):
        """Handles the exit command."""
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea ─────────────────────╮\n╰─❯❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC} {Color.BRIGHTYELLOW}❮❮─╯{Color.ENDC}\n"
        )
        sys.exit(0)

    def _handle_reset_command(self):
        """Handles the reset command."""
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Resetting session...{Color.ENDC}"
        )
        time.sleep(0.5)
        ChatConfig.clear_screen()
        self.chat_history = []
        self.initialize_chat()

    def _handle_clear_command(self):
        """Handles the clear command."""
        ChatConfig.clear_screen()

    def _handle_help_command(self):
        """Handles the help command."""
        ChatConfig.display_help()

    def _handle_reconfigure_command(self):
        """Handles the reconfigure command."""
        config = ChatConfig.reconfigure()
        self.gemini_api_key = config["DEFAULT"]["GeminiAPI"]
        self.ai_service = config["DEFAULT"]["AIService"]
        self.loading_style = config["DEFAULT"]["LoadingStyle"]
        self.instruction_file = config["DEFAULT"]["InstructionFile"]
        self.gemini_model = config["DEFAULT"]["GeminiModel"]
        ChatConfig.initialize_apis(self.gemini_api_key)
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)
        self.initialize_chat()

    def _handle_save_command(self):
        """Handles the save command."""
        file_name = input("Enter the file name to save: ")
        save_log(file_name, self.chat_history)

    def _handle_print_command(self):
        """Handles the print command."""
        file_name = input("Enter the file name to print: ")
        print_log(file_name, self.chat_history)

    def _handle_model_command(self):
        """Handles the model command."""
        if self.change_model():
            self.initialize_chat()
        print(f"\n")

    def save_config(self):
        """
        Save the current configuration to config.ini.
        """
        config = configparser.ConfigParser()
        config.read(ChatConfig.CONFIG_FILE)
        config["DEFAULT"]["AIService"] = self.ai_service
        config["DEFAULT"]["GeminiAPI"] = self.gemini_api_key
        config["DEFAULT"]["GeminiModel"] = self.gemini_model
        with open(ChatConfig.CONFIG_FILE, "w") as configfile:
            config.write(configfile)
        logging.info("Configuration saved.")

    def change_model(self):
        """
        Changes the AI model.

        Returns:
            bool: True if the model was changed successfully, False otherwise.
        """
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.WHITE}Current model: {Color.ENDC}{Color.PASTELPINK}{self.ai_service} - {self.gemini_model}{Color.ENDC}\n"
        )
        change = input(
            f"{Color.BRIGHTYELLOW}Do you want to change the model? (yes/no): {Color.ENDC}"
        ).lower()
        if change == "yes":
            self.ai_service = "gemini"
            if not self.gemini_api_key:
                self.gemini_api_key = input(
                    "Please enter your GEMINI_API_KEY: "
                ).strip()
                self.initializer.gemini_api_key = self.gemini_api_key
                ChatConfig.initialize_apis(self.gemini_api_key)

            try:
                gemini_models = self.get_gemini_models()
            except Exception as e:
                logging.error(f"Error retrieving Gemini models: {e}")
                print(
                    f"{Color.BRIGHTRED}Error retrieving Gemini models. Please check your API key and try again.{Color.ENDC}"
                )
                return False

            if gemini_models:
                print(f"\n{Color.BRIGHTGREEN}Available Gemini models:{Color.ENDC}")
                for i, model in enumerate(gemini_models, 1):
                    print(f"{Color.PASTELPINK}{i}. {model}{Color.ENDC}")

                try:
                    model_choice = input(
                        f"{Color.BRIGHTYELLOW}Enter the model number you want to use: {Color.ENDC}"
                    )
                    model_index = int(model_choice) - 1
                    if 0 <= model_index < len(gemini_models):
                        self.gemini_model = gemini_models[model_index]
                    else:
                        print(
                            f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}"
                        )
                        self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL
                except (ValueError, IndexError):
                    print(
                        f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}"
                    )
                    self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL
            else:
                print(
                    f"{Color.BRIGHTRED}No Gemini models available. Using default model.{Color.ENDC}"
                )
                self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL

            print(
                f"{Color.PASTELPINK}Switched to {self.gemini_model} model. Reinitializing chat...{Color.ENDC}"
            )
            self.save_config()
            self.chat_history = self.chat_history or []
            self.initialize_chat()
            return True
        return False

    def process_user_input(self, chat, user_input):
        """
        Processes user input, sends it to the AI model, and displays the response.

        Args:
            chat: The chat session.
            user_input (str): The user input to process.
        """
        set_stop_loading(False)
        loading_thread = threading.Thread(
            target=loading_animation, args=(self.loading_style,)
        )
        loading_thread.start()

        user_prompt = user_input
        response_text = self.send_message_to_ai(chat, user_input)
        sanitized_response = remove_emojis(response_text)

        self.chat_history.append({"role": "user", "parts": [user_prompt]})
        self.chat_history.append({"role": "model", "parts": [response_text]})

        set_stop_loading(True)
        loading_thread.join()
        sanitized_response = sanitized_response.replace("*", "")
        sanitized_response = re.sub(r"(?i)frea", "𝑓rea", sanitized_response)
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{self.format_response_as_markdown(sanitized_response)}"
        )

    def send_message_to_ai(self, chat, user_input):
        """
        Sends a message to the AI model and returns the response.

        Args:
            chat: The chat session.
            user_input (str): The user input to send.

        Returns:
            str: The AI model's response.
        """
        if self.ai_service == "gemini":
            response = chat.send_message(self.instruction + user_input)
            return response.text if hasattr(response, "text") else str(response)
        return None

    def format_response_as_markdown(self, response_text):
        """
        Formats the response text using Markdown structure.

        Args:
            response_text (str): The response text to format.

        Returns:
            str: The formatted response text.
        """
        response_text = re.sub(r"(?i)\b(frea)\b", r"**\1**", response_text)
        return response_text

    def initialize_chat(self):
        """
        Initializes the chat session.

        Returns:
            Chat: The initialized chat session.
        """
        logging.debug("Initializing chat session")
        self.chat_history = self.chat_history or []
        logging.debug(f"Chat history: {self.chat_history}")
        chat = self.initializer.initialize_chat(self.chat_history)
        if chat is None:
            logging.error("Chat initialization returned None")
            logging.error("Failed to initialize chat. Exiting...")
        return chat

    def get_gemini_models(self):
        """
        Retrieves available Gemini models.

        Returns:
            list: A list of available Gemini model names.
        """
        return self.initializer.get_gemini_models()

    def _determine_ai_service(self):
        """
        Determines the AI service based on available API keys.

        Returns:
            str: The selected AI service.
        """
        if self.initializer.gemini_api_key:
            return "gemini"
        else:
            print(
                f"{Color.BRIGHTRED}No valid API keys found. Please provide at least one API key.{Color.ENDC}"
            )
            self.gemini_api_key = input("Please enter your GEMINI_API_KEY: ").strip()
            if self.gemini_api_key:
                self.initializer.gemini_api_key = self.gemini_api_key
                ChatConfig.initialize_apis(self.gemini_api_key)
                return "gemini"
            else:
                raise ValueError("No valid API keys provided. Exiting...")


if __name__ == "__main__":
    chat_app = AIChat()
    chat_app.generate_chat()
