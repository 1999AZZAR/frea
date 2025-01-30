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
import openai
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
        self.gemini_api_key = self.initializer.gemini_api_key
        self.groq_api_key = self.initializer.groq_api_key
        self.ai_service = self.initializer.ai_service
        self.model = self.initializer.model
        self.chat_history = []
        self.loading_style = self.initializer.loading_style
        self.instruction = self.initializer.instruction

        # Register cleanup function
        atexit.register(self.cleanup)

    def cleanup(self):
        """
        Cleans up resources when the application exits.
        """
        pass  # No cleanup needed for OpenAI client

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
        elif command == ChatConfig.SERVICE_COMMAND:
            self._handle_change_ai_service()
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
        self.groq_api_key = config["DEFAULT"]["GroqAPI"]
        self.ai_service = config["DEFAULT"]["AIService"]
        self.loading_style = config["DEFAULT"]["LoadingStyle"]
        self.instruction_file = config["DEFAULT"]["InstructionFile"]
        self.model = config["DEFAULT"]["AIModel"]
        self.initializer = ChatInitializer()  # Reinitialize with new config
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

    def _handle_change_ai_service(self):
        """
        Changes the AI service (Gemini or Groq) and updates the config file.

        Returns:
            bool: True if the service was changed successfully, False otherwise.
        """
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.WHITE}Current AI service: {Color.ENDC}{Color.PASTELPINK}{self.ai_service}{Color.ENDC}\n"
        )
        change = input(
            f"{Color.BRIGHTYELLOW}Do you want to change the AI service? (yes/no): {Color.ENDC}"
        ).lower()
        if change == "yes":
            new_service = input(f"Enter the new AI service (gemini/groq): ").lower()
            if new_service not in ["gemini", "groq"]:
                print(
                    f"{Color.BRIGHTRED}Invalid AI service. Must be 'gemini' or 'groq'.{Color.ENDC}"
                )
                return False

            # Update the AI service
            self.ai_service = new_service

            # Load the current config
            config = ChatConfig.initialize_config()
            config["DEFAULT"]["AIService"] = new_service

            # Save the updated config
            ChatConfig.save_config(config)

            # Reinitialize the chat with the new service
            self.initializer = ChatInitializer()
            self.model = self.initializer.model
            print(
                f"{Color.PASTELPINK}Switched to {self.ai_service} service. Reinitializing chat...{Color.ENDC}"
            )
            return True
        return False

    def change_model(self):
        """
        Changes the AI model and updates the config file.

        Returns:
            bool: True if the model was changed successfully, False otherwise.
        """
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.WHITE}Current model: {Color.ENDC}{Color.PASTELPINK}{self.model}{Color.ENDC}\n"
        )
        change = input(
            f"{Color.BRIGHTYELLOW}Do you want to change the model? (yes/no): {Color.ENDC}"
        ).lower()
        if change == "yes":
            try:
                models = self.initializer.get_models()
            except Exception as e:
                logging.error(f"Error retrieving models: {e}")
                print(
                    f"{Color.BRIGHTRED}Error retrieving models. Please check your API key and try again.{Color.ENDC}"
                )
                return False

            if models:
                print(f"\n{Color.BRIGHTGREEN}Available models:{Color.ENDC}")
                for i, model in enumerate(models, 1):
                    print(f"{Color.PASTELPINK}{i}. {model}{Color.ENDC}")

                try:
                    model_choice = input(
                        f"{Color.BRIGHTYELLOW}Enter the model number you want to use: {Color.ENDC}"
                    )
                    model_index = int(model_choice) - 1
                    if 0 <= model_index < len(models):
                        self.model = models[model_index]
                    else:
                        print(
                            f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}"
                        )
                        # Use the default model for the current AI service
                        self.model = (
                            ChatConfig.DEFAULT_GEMINI_MODEL
                            if self.ai_service == "gemini"
                            else ChatConfig.DEFAULT_GROQ_MODEL
                        )
                except (ValueError, IndexError):
                    print(
                        f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}"
                    )
                    # Use the default model for the current AI service
                    self.model = (
                        ChatConfig.DEFAULT_GEMINI_MODEL
                        if self.ai_service == "gemini"
                        else ChatConfig.DEFAULT_GROQ_MODEL
                    )
            else:
                print(
                    f"{Color.BRIGHTRED}No models available. Using default model.{Color.ENDC}"
                )
                # Use the default model for the current AI service
                self.model = (
                    ChatConfig.DEFAULT_GEMINI_MODEL
                    if self.ai_service == "gemini"
                    else ChatConfig.DEFAULT_GROQ_MODEL
                )

            # Load the current config
            config = ChatConfig.initialize_config()
            config["DEFAULT"]["AIModel"] = self.model

            # Save the updated config
            ChatConfig.save_config(config)

            print(
                f"{Color.PASTELPINK}Switched to {self.model} model. Reinitializing chat...{Color.ENDC}"
            )
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

        # Append user input and AI response to chat history
        self.chat_history.append({"role": "user", "content": user_prompt})
        self.chat_history.append({"role": "assistant", "content": response_text})

        set_stop_loading(True)
        loading_thread.join()
        sanitized_response = sanitized_response.replace("*", "")
        sanitized_response = re.sub(r"(?i)frea", "𝑓rea", sanitized_response)
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{self.format_response_as_markdown(sanitized_response)}"
        )

    def truncate_chat_history(self, chat_history, max_tokens=2048):
        """
        Truncates the chat history to stay within the token limit.

        Args:
            chat_history (list): The chat history to truncate.
            max_tokens (int): The maximum number of tokens allowed.

        Returns:
            list: The truncated chat history.
        """
        # Calculate the total token count (this is a simplified example)
        total_tokens = sum(len(message["content"].split()) for message in chat_history)

        # Remove older messages until the token count is within the limit
        while total_tokens > max_tokens and len(chat_history) > 1:
            removed_message = chat_history.pop(
                1
            )  # Remove the oldest user-assistant pair
            total_tokens -= len(removed_message["content"].split())

        return chat_history

    def send_message_to_ai(self, chat, user_input):
        """
        Sends a message to the AI model and returns the response.

        Args:
            chat: The chat session.
            user_input (str): The user input to send.

        Returns:
            str: The AI model's response.
        """
        # Get the generation config and safety settings from ChatConfig
        generation_config = ChatConfig.generation_config()

        # Prepare the messages for the API request
        messages = [
            {"role": "system", "content": self.instruction}
        ]  # System instruction

        # Truncate the chat history to avoid exceeding token limits
        truncated_history = self.truncate_chat_history(self.chat_history.copy())
        messages.extend(truncated_history)  # Add the truncated chat history

        messages.append(
            {"role": "user", "content": user_input}
        )  # Add the latest user input

        # Create the request payload with the necessary configurations
        response = self.initializer.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            max_tokens=generation_config.get("max_output_tokens", 2048),
            temperature=generation_config.get("temperature", 0.25),
            top_p=generation_config.get("top_p", 0.65),
            # frequency_penalty=generation_config.get("frequency_penalty", 1.2), # only works on Groq
        )

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
        return full_response

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

    def print_log(file_name, chat_history):
        """
        Saves the chat history to a file in Markdown format.

        Args:
            file_name (str): The name of the file to save the chat history.
            chat_history (list): The chat history to save.
        """
        if not file_name.endswith(".md"):
            file_name += ".md"

        try:
            with open(file_name, "w", encoding="utf-8") as file:
                file.write("# Conversation Log\n\n")
                for entry in chat_history:
                    role = entry["role"]
                    content = entry["content"]
                    if isinstance(content, list):
                        content = "\n".join(content)
                    file.write(f"## {role.capitalize()}:\n{content}\n\n")
            print(f"{Color.BRIGHTGREEN}Chat history saved to {file_name}{Color.ENDC}")
        except Exception as e:
            print(f"{Color.BRIGHTRED}Error saving chat history: {e}{Color.ENDC}")


if __name__ == "__main__":
    chat_app = AIChat()
    chat_app.generate_chat()
