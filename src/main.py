# ruff: noqa: E402
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(1, str(_SRC_DIR))

import threading
import logging
import time
import re
from logging.handlers import RotatingFileHandler
from color import Color
from chat_initializer import ChatInitializer
from chat_config import ChatConfig
from utils import (
    run_subprocess,
    loading_animation,
    set_stop_loading,
)
import openai
from printer import save_log, print_log
import atexit
import os  # Added to handle file commands
import agent_tools as tools
import json

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
                    pass
                    print(f"{Color.AQUA}╰─❯❯ {Color.ENDC}", end="")
                else:
                    print(f"{Color.AQUA}╭─ master \n╰─❯❯ {Color.ENDC}", end="")

                # Use readline for input with history navigation
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

                # Handle send file commands (e.g., send <file> or /send <file>)
                if user_input.strip().lower().startswith(
                    "send "
                ) or user_input.strip().startswith("/send "):
                    parts = user_input.strip().split(maxsplit=1)
                    filename = parts[1] if len(parts) > 1 else None
                    if not filename:
                        print(f"{Color.BRIGHTRED}Usage: send <file_path>{Color.ENDC}")
                        user_input = ""
                        multiline_mode = False
                        continue
                    filepath = os.path.expanduser(filename)
                    if not os.path.exists(filepath):
                        print(
                            f"{Color.BRIGHTRED}File not found: {filename}{Color.ENDC}"
                        )
                        user_input = ""
                        multiline_mode = False
                        continue
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        print(f"{Color.BRIGHTRED}Error reading file: {e}{Color.ENDC}")
                        user_input = ""
                        multiline_mode = False
                        continue
                    prompt = (
                        f"Please review the following file: {filename}\n\n{content}"
                    )
                    self.process_user_input(chat, prompt)
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
                    print("\n")
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
        stripped = user_input.strip()
        lower = stripped.lower()
        if lower.startswith("wiki "):
            res = tools.wiki(stripped.split(maxsplit=1)[1])
            print(res)
            return True
        elif lower.startswith("calc "):
            res = tools.calc(stripped.split(maxsplit=1)[1])
            print(res)
            return True
        elif lower.startswith("ls"):
            parts = stripped.split(maxsplit=1)
            path = parts[1] if len(parts) > 1 else "."
            res = tools.ls(path)
            if res:
                print(res)
            return True
        elif lower.startswith("cat "):
            res = tools.cat(stripped.split(maxsplit=1)[1])
            print(res)
            return True
        elif lower.startswith("head "):
            parts = stripped.split()
            path = parts[1] if len(parts) > 1 else ""
            n = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 10
            res = tools.head(path, n)
            print(res)
            return True
        elif lower.startswith("tail "):
            parts = stripped.split()
            path = parts[1] if len(parts) > 1 else ""
            n = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 10
            res = tools.tail(path, n)
            print(res)
            return True
        elif lower.startswith("grep "):
            parts = stripped.split(maxsplit=2)
            pattern = parts[1] if len(parts) > 1 else ""
            path = parts[2] if len(parts) > 2 else "."
            res = tools.grep(pattern, path)
            print(res)
            return True
        elif lower.startswith("write "):
            parts = stripped.split(maxsplit=2)
            path = parts[1] if len(parts) > 1 else ""
            content = parts[2] if len(parts) > 2 else ""
            res = tools.write_file(path, content)
            print(res)
            return True
        elif lower.startswith("append "):
            parts = stripped.split(maxsplit=2)
            path = parts[1] if len(parts) > 1 else ""
            content = parts[2] if len(parts) > 2 else ""
            res = tools.append_file(path, content)
            print(res)
            return True
        elif lower.startswith("delete "):
            res = tools.delete_file(stripped.split(maxsplit=1)[1])
            print(res)
            return True
        elif lower.startswith("move "):
            parts = stripped.split(maxsplit=2)
            src = parts[1] if len(parts) > 1 else ""
            dst = parts[2] if len(parts) > 2 else ""
            res = tools.move(src, dst)
            print(res)
            return True
        elif lower.startswith("copy "):
            parts = stripped.split(maxsplit=2)
            src = parts[1] if len(parts) > 1 else ""
            dst = parts[2] if len(parts) > 2 else ""
            res = tools.copy(src, dst)
            print(res)
            return True
        elif lower.startswith("vim "):
            res = tools.vim(stripped.split(maxsplit=1)[1])
            print(res)
            return True
        elif command == ChatConfig.EXIT_COMMAND:
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
        elif command == ChatConfig.EXPORT_COMMAND:
            self._handle_export_command()
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

    def _handle_export_command(self):
        """Handles the export command: extracts code blocks and saves to a file."""
        file_name = input("Enter the file name to export code blocks: ")
        if not file_name:
            print(f"{Color.BRIGHTRED}No file name provided.{Color.ENDC}")
            return
        # Extract code blocks from assistant messages
        combined = "".join(
            entry["content"]
            for entry in self.chat_history
            if entry.get("role") == "assistant"
        )
        pattern = r"```(?:[a-zA-Z0-9_#+-]*\n)?(.*?)```"
        blocks = re.findall(pattern, combined, flags=re.DOTALL)
        if not blocks:
            print(
                f"{Color.BRIGHTYELLOW}No code blocks found in the conversation.{Color.ENDC}"
            )
            return
        code_content = "\n\n".join(block.strip() for block in blocks)
        # Ensure export directory exists
        os.makedirs(ChatConfig.EXPORT_FOLDER, exist_ok=True)
        filepath = os.path.join(ChatConfig.EXPORT_FOLDER, file_name)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code_content)
            print(f"{Color.BRIGHTGREEN}Exported code blocks to {filepath}{Color.ENDC}")
        except Exception as e:
            print(f"{Color.BRIGHTRED}Error exporting code blocks: {e}{Color.ENDC}")

    def _handle_model_command(self):
        """Handles the model command."""
        if self.change_model():
            self.initialize_chat()

    def _handle_change_ai_service(self):
        """
        Changes the AI service (Gemini or Groq) and updates the config file.
        """
        print(
            f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.WHITE}Current AI service: {Color.ENDC}{Color.PASTELPINK}{self.ai_service}{Color.ENDC}\n"
        )
        change = input(
            f"{Color.BRIGHTYELLOW}Do you want to change the AI service? (yes/no): {Color.ENDC}"
        ).lower()
        if change != "yes":
            return False

        # Provider selection by number
        providers = ["gemini", "groq"]
        print(f"\n{Color.BRIGHTYELLOW}Select AI provider:{Color.ENDC}")
        for idx, prov in enumerate(providers, 1):
            print(f"  {idx}. {prov}")
        choice = input(f"{Color.BRIGHTYELLOW}Enter provider number: {Color.ENDC}")
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(providers):
                raise ValueError()
            new_service = providers[idx]
        except ValueError:
            print(
                f"{Color.BRIGHTRED}Invalid choice. Aborting provider change.{Color.ENDC}"
            )
            return False

        # Update config with new service
        config = ChatConfig.initialize_config()
        config["DEFAULT"]["AIService"] = new_service
        ChatConfig.save_config(config)

        # Reinitialize initializer for new service
        self.initializer = ChatInitializer()

        # Model selection for chosen provider
        models = self.initializer.get_models() or []
        if models:
            print(
                f"\n{Color.BRIGHTGREEN}Available models for {new_service}:{Color.ENDC}"
            )
            for i, m in enumerate(models, 1):
                print(f"  {i}. {m}")
            choice = input(f"{Color.BRIGHTYELLOW}Enter model number: {Color.ENDC}")
            try:
                m_idx = int(choice) - 1
                if m_idx < 0 or m_idx >= len(models):
                    raise ValueError()
                chosen_model = models[m_idx]
            except ValueError:
                print(
                    f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}"
                )
                chosen_model = (
                    ChatConfig.DEFAULT_GEMINI_MODEL
                    if new_service == "gemini"
                    else ChatConfig.DEFAULT_GROQ_MODEL
                )
        else:
            print(
                f"{Color.BRIGHTYELLOW}No models retrieved. Using default model.{Color.ENDC}"
            )
            chosen_model = (
                ChatConfig.DEFAULT_GEMINI_MODEL
                if new_service == "gemini"
                else ChatConfig.DEFAULT_GROQ_MODEL
            )

        # Save chosen model
        config["DEFAULT"]["AIModel"] = chosen_model
        ChatConfig.save_config(config)

        # Update instance settings
        self.ai_service = new_service
        self.model = chosen_model
        print(
            f"{Color.PASTELPINK}Switched to provider '{new_service}' and model '{chosen_model}'. Reinitializing chat...{Color.ENDC}"
        )
        time.sleep(1)
        ChatConfig.clear_screen()
        return True

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
            time.sleep(1)
            ChatConfig.clear_screen()
            self.chat_history = self.chat_history or []
            self.initialize_chat()
            return True
        return False

    def extract_wikipedia_query(self, user_input):
        """
        Extracts the Wikipedia query from the user input based on the specified rules.

        Args:
            user_input (str): The user input to parse.

        Returns:
            str: The extracted Wikipedia query, or None if no valid query is found.
        """
        # Rule 1: Check for up to three phrases enclosed in double quotes
        quoted_phrases = re.findall(r'"(.*?)"', user_input)
        if quoted_phrases:
            # Use the first quoted phrase as the query
            return quoted_phrases[0]

        # Rule 2: Check for text enclosed in backticks
        backtick_phrases = re.findall(r"`(.*?)`", user_input)
        if backtick_phrases:
            # Use the first backtick phrase as the query
            return backtick_phrases[0]

        # Rule 3: Use the last two words of the prompt if no quotes or backticks are found
        words = user_input.split()
        if len(words) >= 2:
            return " ".join(words[-2:])

        return None

    def process_user_input(self, chat, user_input):
        """
        Processes user input, sends it to the AI model, and displays the response.

        Args:
            chat: The chat session.
            user_input (str): The user input to process.
        """
        user_prompt = user_input

        # Check if the user wants to use Wikipedia
        if "-wiki" in user_input.lower():
            # Extract the Wikipedia query from the user input
            query = self.extract_wikipedia_query(user_input)
            if query:
                # Query Wikipedia for additional information
                wiki_info = self.initializer.query_wikipedia(query)
                if wiki_info:
                    # Append Wikipedia information to the user input
                    user_input += f"\n\nHere's some additional information from Wikipedia:\n{wiki_info}"

        print()  # blank line before frea prompt
        print(f"{Color.LIGHTPURPLE}╭─ 𝑓rea\n╰─❯❯ {Color.ENDC}", end="", flush=True)
        response_text = self.send_message_to_ai(chat, user_input)
        print()  # blank line after AI response
        # Append user input and AI response to chat history
        self.chat_history.append({"role": "user", "content": user_prompt})
        self.chat_history.append({"role": "assistant", "content": response_text})

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

        messages.append({"role": "user", "content": user_input})

        # Inject tool usage instructions into the system prompt
        tool_instructions = """
You have access to these tools:
- wiki(query: string, sentences: int)
- calc(expression: string)
- ls(path: string)
- cat(file_path: string)
- head(file_path: string, lines: int)
- tail(file_path: string, lines: int)
- grep(pattern: string, path: string)
- write_file(file_path: string, content: string)
- append_file(file_path: string, content: string)
- delete_file(file_path: string)
- move(src: string, dst: string)
- copy(src: string, dst: string)

When you want to use a tool, reply with only JSON:
{"tool":"<name>","args":{...}}
and nothing else.
"""
        messages[0]["content"] += "\n" + tool_instructions

        # Call model and spinner
        set_stop_loading(False)
        spinner = threading.Thread(
            target=loading_animation, args=(self.loading_style,), daemon=True
        )
        spinner.start()
        # Retry mechanism for API call
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.initializer.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=generation_config.get("max_output_tokens", 2048),
                    temperature=generation_config.get("temperature", 0.25),
                    top_p=generation_config.get("top_p", 0.65),
                )
                break
            except openai.error.OpenAIError as e:
                logging.warning(f"API request failed ({attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                else:
                    set_stop_loading(True)
                    spinner.join()
                    return f"Error calling AI API after {max_retries} attempts: {e}"
        set_stop_loading(True)
        spinner.join()
        output = response.choices[0].message.content.strip()

        # Detect and run tool if model returned JSON
        try:
            # strip markdown fences or any wrapping and extract JSON object
            match = re.search(r"\{.*\}", output, re.DOTALL)
            payload = match.group() if match else output
            call = json.loads(payload)
            name = call.get("tool")
            args = call.get("args", {})
            if name and hasattr(tools, name):
                result = getattr(tools, name)(**args)
                # Provide tool output back to model for final answer
                messages.append({"role": "assistant", "content": output})
                messages.append({"role": "function", "name": name, "content": result})
                # Retry mechanism for follow-up API call
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        follow = self.initializer.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            max_tokens=generation_config.get("max_output_tokens", 2048),
                            temperature=generation_config.get("temperature", 0.25),
                            top_p=generation_config.get("top_p", 0.65),
                        )
                        break
                    except openai.error.OpenAIError as e:
                        logging.warning(
                            f"Follow-up API request failed ({attempt+1}/{max_retries}): {e}"
                        )
                        if attempt < max_retries - 1:
                            time.sleep(2**attempt)
                            continue
                        else:
                            return f"Error calling AI API after tool result: {e}"
                final = follow.choices[0].message.content
                print(final)
                return final
        except (json.JSONDecodeError, AttributeError):
            pass
        # Otherwise, just return model output
        print(output)
        return output

    def format_response_as_markdown(self, response_text):
        """
        Formats the response text using Markdown structure.

        Args:
            response_text (str): The response text to format.

        Returns:
            str: The formatted response text.
        """
        return re.sub(r"(?i)\b(frea)\b", r"**\1**", response_text)

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


def main() -> int:
    """Modernized entrypoint for Frea CLI and interactive TUI harness."""
    try:
        from src.runner import run_cli
        from src.cli import CLIConfig
        from src.config import load_frea_config
        from src.agent import AgentLoop
        from src.executor import ToolExecutor
        from src.providers import get_provider
        from src.tui import InteractiveREPL
    except ImportError:
        chat_app = AIChat()
        chat_app.generate_chat()
        return 0

    def headless_run(config: CLIConfig) -> int:
        frea_cfg = load_frea_config(config.config_path)
        model_name = config.model or frea_cfg.get("model") or "openrouter/auto"
        provider_name = frea_cfg.get("provider", "openrouter")
        auto_approve = config.yes or frea_cfg.get("auto_approve", False)

        provider_key = (
            "openrouter"
            if "openrouter" in model_name.lower()
            else (model_name.split("/")[0] if "/" in model_name else provider_name)
        )
        try:
            provider = get_provider(provider_key, model=model_name)
        except Exception:
            provider = get_provider("openrouter", model=model_name)
        executor = ToolExecutor(auto_approve=auto_approve)
        agent = AgentLoop(provider=provider, executor=executor)
        result = agent.run(config.prompt)
        print(result.final_answer)
        return 0 if result.success else 1

    def interactive_run(config: CLIConfig) -> int:
        from src.commands import SessionState

        frea_cfg = load_frea_config(config.config_path)
        model_name = config.model or frea_cfg.get("model") or "openrouter/auto"
        provider_name = frea_cfg.get("provider", "openrouter")
        auto_approve = config.yes or frea_cfg.get("auto_approve", False)

        provider_key = (
            "openrouter"
            if "openrouter" in model_name.lower()
            else (model_name.split("/")[0] if "/" in model_name else provider_name)
        )
        try:
            provider = get_provider(provider_key, model=model_name)
        except Exception:
            chat_app = AIChat()
            chat_app.generate_chat()
            return 0
        executor = ToolExecutor(auto_approve=auto_approve)
        agent = AgentLoop(provider=provider, executor=executor)
        session = SessionState(current_model=model_name, current_provider=provider_key)
        repl = InteractiveREPL(agent_loop=agent, session=session)
        return repl.run_repl()

    return run_cli(
        interactive_handler=interactive_run,
        headless_handler=headless_run,
    )


if __name__ == "__main__":
    sys.exit(main())
