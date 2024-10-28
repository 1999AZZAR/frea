import sys, threading, logging, time, re
from logging.handlers import RotatingFileHandler
from color import Color
from chat_initializer import ChatInitializer
from chat_config import ChatConfig
from utils import remove_emojis, run_subprocess, loading_animation, set_stop_loading, cursor_hide, cursor_show
import google.generativeai as genai
import configparser
from printer import print_log, save_log

# Configure logging with RotatingFileHandler
log_handler = RotatingFileHandler('./logs/error.log', maxBytes=0.5*1024*1024, backupCount=3)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

class AIChat:
    def __init__(self):
        self.initializer = ChatInitializer()
        self.gemini_api_key = self.initializer.gemini_api_key or ""
        self.ai_service = self._determine_ai_service()
        self.gemini_model = self.initializer.gemini_model
        self.chat_history = []
        self.loading_style = self.initializer.loading_style
        self.instruction = self.initializer.instruction

    def generate_chat(self):
        """model generation response flow"""
        chat = self.initialize_chat()
        if chat is None:
            print(f"{Color.BRIGHTRED}Failed to initialize chat. Exiting...{Color.ENDC}")
            return
        user_input = ""
        multiline_mode = False

        while True:
            try:
                """multiline automation"""
                if multiline_mode:
                    print(f"{Color.BLUE}╰─❯❯ {Color.ENDC}", end="")
                else:
                    print(f"{Color.BLUE}╭─ 𝔲ser \n╰─❯❯ {Color.ENDC}", end="")
                user_input_line = input()

                if user_input_line.endswith("\\"):
                    user_input += user_input_line.rstrip("\\") + "\n"
                    multiline_mode = True
                    continue
                else:
                    user_input += user_input_line

                if self.handle_special_commands(user_input):
                    user_input = ""
                    multiline_mode = False
                    continue

                if not user_input:
                    print(f'\n{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.LIGHTRED}Please enter your command/prompt{Color.ENDC}\n')
                    user_input = ""
                    multiline_mode = False
                    continue

                if user_input.strip().lower().startswith("run ") or user_input.strip().startswith("/"):
                    """Run a subprocess command"""
                    if user_input.strip().startswith("/"):
                        command = user_input[1:].strip()
                    else:
                        command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.LIGHTRED}Executing 𝔲ser Command{Color.ENDC}\n')
                    run_subprocess(command)
                    user_input = ""
                    multiline_mode = False
                else:
                    self.process_user_input(chat, user_input)
                    user_input = ""
                    multiline_mode = False

            except KeyboardInterrupt:
                print("\nKeyboard Interrupt")
                break
            except Exception as e:
                set_stop_loading(True)
                logging.error(f"Error during chat generation: {e}", exc_info=True)
                print(f"\n{Color.BRIGHTRED}An error occurred. Please check the logs for more details.{Color.ENDC}")
                break

    def save_config(self):
        """Save the current configuration to config.ini"""
        config = configparser.ConfigParser()
        config.read(ChatConfig.CONFIG_FILE)
        config['DEFAULT']['AIService'] = self.ai_service
        config['DEFAULT']['GeminiAPI'] = self.gemini_api_key
        config['DEFAULT']['GeminiModel'] = self.gemini_model
        with open(ChatConfig.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        logging.info("Configuration saved.")

    def handle_special_commands(self, user_input):
        """Handle special commands"""
        if user_input.strip().lower() == ChatConfig.EXIT_COMMAND:
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}\n")
            sys.exit(0)

        elif user_input.strip().lower() == ChatConfig.RESET_COMMAND:
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.PASTELPINK}Resetting session...{Color.ENDC}\n")
            time.sleep(0.5)
            ChatConfig.clear_screen()
            self.chat_history = []
            self.initialize_chat()
            return True

        elif user_input.strip().lower() == ChatConfig.CLEAR_COMMAND:
            ChatConfig.clear_screen()
            return True

        elif user_input.strip().lower() == ChatConfig.HELP_COMMAND:
            ChatConfig.display_help()
            return True

        elif user_input.strip().lower() == ChatConfig.RECONFIGURE_COMMAND:
            config = ChatConfig.reconfigure()
            self.gemini_api_key = config['DEFAULT']['GeminiAPI']
            self.openai_api_key = config['DEFAULT']['OpenAIAPI']
            self.ai_service = config['DEFAULT']['AIService']
            self.loading_style = config['DEFAULT']['LoadingStyle']
            self.instruction_file = config['DEFAULT']['InstructionFile']
            self.gemini_model = config['DEFAULT']['GeminiModel']
            ChatConfig.initialize_apis(self.gemini_api_key)
            self.instruction = ChatConfig.chat_instruction(self.instruction_file)
            self.initialize_chat()
            return True

        elif user_input.strip().lower() == ChatConfig.SAVE_COMMAND:
            file_name = input("Enter the file name to save: ")
            save_log(file_name, self.chat_history)
            return True

        elif user_input.strip().lower() == ChatConfig.PRINT_COMMAND:
            file_name = input("Enter the file name to print: ")
            print_log(file_name, self.chat_history)
            return True

        elif user_input.strip().lower() == ChatConfig.MODEL_COMMAND:
            if self.change_model():
                self.initialize_chat()
            print(f'\n')
            return True

        return False

    def change_model(self):
        """Change the AI model"""
        print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{Color.WHITE}Current model: {Color.ENDC}{Color.PASTELPINK}{self.ai_service} - {self.gemini_model}{Color.ENDC}")
        change = input(f"{Color.BRIGHTYELLOW}Do you want to change the model? (yes/no): {Color.ENDC}").lower()
        if change == 'yes':
            self.ai_service = 'gemini'
            if not self.gemini_api_key:
                self.gemini_api_key = input("Please enter your GEMINI_API_KEY: ").strip()
                self.initializer.gemini_api_key = self.gemini_api_key
                ChatConfig.initialize_apis(self.gemini_api_key)
            try:
                gemini_models = self.get_gemini_models()
            except Exception as e:
                logging.error(f"Error retrieving Gemini models: {e}")
                print(f"{Color.BRIGHTRED}Error retrieving Gemini models. Please check your API key and try again.{Color.ENDC}")
                self.gemini_api_key = input("Please enter your GEMINI_API_KEY: ").strip()
                self.initializer.gemini_api_key = self.gemini_api_key
                ChatConfig.initialize_apis(self.gemini_api_key)
                gemini_models = self.get_gemini_models()
            if gemini_models:
                print(f"\n{Color.BRIGHTGREEN}Available Gemini models:{Color.ENDC}")
                for i, model in enumerate(gemini_models, 1):
                    print(f"{Color.PASTELPINK}{i}. {model}{Color.ENDC}")
                model_choice = input(f"{Color.BRIGHTYELLOW}Enter the model number you want to use: {Color.ENDC}")
                try:
                    self.gemini_model = gemini_models[int(model_choice) - 1]
                except (ValueError, IndexError):
                    print(f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}")
                    self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL
            else:
                print(f"{Color.BRIGHTRED}No Gemini models available. Using default model.{Color.ENDC}")
                self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL

            print(f"{Color.PASTELPINK}Switched to {self.gemini_model.capitalize()} model. Reinitializing chat...{Color.ENDC}")
            self.save_config()
            self.chat_history = self.chat_history or []
            self.initialize_chat()
            return True
        return False

    def extract_quoted_texts(self, text):
        return re.findall(r'"([^"]*)"', text)

    def process_user_input(self, chat, user_input):
        """Send user input to the language model and print the response"""
        set_stop_loading(False)
        loading_thread = threading.Thread(target=loading_animation, args=(self.loading_style,))
        loading_thread.start()
        user_prompt = user_input

        # Detect if there is any text enclosed in backticks
        backtick_texts = re.findall(r'`([^`]+)`', user_input)

        wiki_success = False

        if user_input.strip().endswith("-wiki") or backtick_texts:
            # Extract quoted texts if the input ends with "-wiki"
            if not backtick_texts:
                quoted_texts = self.extract_quoted_texts(user_input)
            else:
                quoted_texts = backtick_texts

            wiki_summaries = []
            for i, query in enumerate(quoted_texts[:3]):  # Limit to 3 queries
                logging.info(f"Querying Wikipedia with: {query}")
                wiki_summary = self.initializer.query_wikipedia(query)
                if wiki_summary:
                    wiki_summaries.append(f"Info for '{query}': {wiki_summary}")
                    wiki_success = True
                    logging.info(f"Wikipedia query {i+1} successful")
                else:
                    logging.info(f"Wikipedia query {i+1} returned no results")

            if not quoted_texts:
                query = ' '.join(user_input.strip()[:-5].strip().split()[-2:])
                logging.info(f"Querying Wikipedia with: {query}")
                wiki_summary = self.initializer.query_wikipedia(query)
                if wiki_summary:
                    wiki_summaries.append(f"Info for '{query}': {wiki_summary}")
                    wiki_success = True
                    logging.info("Wikipedia query successful")
                else:
                    logging.info("Wikipedia query returned no results")

            if wiki_success:
                # Remove the "-wiki" texts from the user input
                if user_input.strip().endswith("-wiki"):
                    user_input = user_input[:-5].strip()
                user_input += "\nContext: " + "\n".join(wiki_summaries) + "always give me back all the link(s)"
            else:
                if user_input.strip().endswith("-wiki"):
                    user_input = user_input[:-5].strip()
                else:
                    user_input = user_input
        else:
            user_input = user_input

        response_text = self.send_message_to_ai(chat, user_input)
        sanitized_response = remove_emojis(response_text)

        ai_success = bool(response_text)
        logging.info(f"Wiki Success: {wiki_success}, AI Success: {ai_success}")
        self.chat_history.append({"role": "user", "parts": [user_prompt]})
        self.chat_history.append({"role": "model", "parts": [response_text]})

        set_stop_loading(True)
        loading_thread.join()
        sanitized_response = sanitized_response.replace('*', '')
        sanitized_response = re.sub(r'(?i)frea', '𝑓rea', sanitized_response)
        print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯❯ {Color.ENDC}{self.format_response_as_markdown(sanitized_response)}')

    def send_message_to_ai(self, chat, user_input):
        """Send message to the AI service and get the response"""
        if self.ai_service == 'gemini':
            response = chat.send_message(self.instruction + user_input)
            if isinstance(response, str):
                return response
            else:
                return response.text
        return None

    def format_response_as_markdown(self, response_text):
        """Format the response text using Markdown structure"""
        response_text = re.sub(r'(?i)\b(frea)\b', r'**\1**', response_text)
        return response_text

    def initialize_chat(self):
        """Initialize the chat session"""
        logging.debug("Initializing chat session")
        self.chat_history = self.chat_history or []
        logging.debug(f"Chat history: {self.chat_history}")
        chat = self.initializer.initialize_chat(self.chat_history)
        if chat is None:
            logging.error("Chat initialization returned None")
            logging.error("Failed to initialize chat. Exiting...")
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        return self.initializer.get_gemini_models()

    def _determine_ai_service(self):
        """Determine the AI service based on available API keys"""
        if self.initializer.gemini_api_key:
            return 'gemini'

        else:
            print(f"{Color.BRIGHTRED}No valid API keys found. Please provide at least one API key.{Color.ENDC}")
            self.gemini_api_key = input("Please enter your GEMINI_API_KEY : ").strip()
            if self.gemini_api_key:
                self.initializer.gemini_api_key = self.gemini_api_key
                ChatConfig.initialize_apis(self.gemini_api_key)
                return 'gemini'

            else:
                raise ValueError("No valid API keys provided. Exiting...")

if __name__ == "__main__":
     chat_app = AIChat()
     chat_app.generate_chat()
