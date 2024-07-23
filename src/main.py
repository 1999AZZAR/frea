import os, readline, termios, tty, sys, threading, configparser, datetime, json, logging, time, re
from logging.handlers import RotatingFileHandler
from color import Color
from chat_initializer import ChatInitializer
from chat_config import ChatConfig
from terminal_utils import cursor_hide, cursor_show
from utils import remove_emojis, run_subprocess, loading_animation, set_stop_loading, combine_responses
import google.generativeai as genai
import openai
from openai import OpenAI

# Configure logging with RotatingFileHandler
log_handler = RotatingFileHandler('error.log', maxBytes=0.5*1024*1024, backupCount=3)
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.DEBUG)

class AIChat:
    def __init__(self):
        self.initializer = ChatInitializer()
        self.gemini_api_key = self.initializer.gemini_api_key or ""
        self.openai_api_key = self.initializer.openai_api_key or ""
        self.ai_service = self._determine_ai_service()
        self.gemini_model = self.initializer.gemini_model
        self.gpt_model = self.initializer.gpt_model
        self.langchain_client = self.initializer.langchain_client
        self.chat_history = []  # Unified chat history
        self.loading_style = self.initializer.loading_style
        self.instruction = self.initializer.instruction
        self.openai_client = self.initializer.openai_client
        self.conversation_log = []

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
                    print(f"{Color.BLUE}╰─❯ {Color.ENDC}", end="")
                else:
                    print(f"{Color.BLUE}╭─ 𝔲ser \n╰─❯ {Color.ENDC}", end="")
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
                    print(f'\n{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Please enter your command/prompt{Color.ENDC}\n')
                    user_input = ""
                    multiline_mode = False
                    continue

                if user_input.strip().lower().startswith("run "):
                    """Run a subprocess command"""
                    command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Executing 𝔲ser Command{Color.ENDC}\n')
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
                logging.error(f"Error during chat generation: {e}")
                logging.error(f"Error during chat generation: {e}", exc_info=True)
                print(f"{Color.BRIGHTRED}An error occurred. Please check the logs for more details.{Color.ENDC}")
                break

    def handle_special_commands(self, user_input):
        """Handle special commands"""
        if user_input.strip().lower() == ChatConfig.EXIT_COMMAND:
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}\n")
            sys.exit(0)
            sys.exit(0)
        elif user_input.strip().lower() == ChatConfig.RESET_COMMAND:
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Resetting session...{Color.ENDC}\n")
            time.sleep(0.5)
            ChatConfig.clear_screen()
            self.chat_history = []
            self.initialize_chat()
            self.conversation_log = []
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
            self.gpt_model = config['DEFAULT']['GPTModel']
            ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
            self.instruction = ChatConfig.chat_instruction(self.instruction_file)
            self.initialize_chat()
            self.conversation_log = []
            return True
        elif user_input.strip().lower() == ChatConfig.PRINT_COMMAND:
            """Save conversation log to a JSON file"""
            current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file_name = f"{ChatConfig.LOG_FOLDER}/log_{current_datetime}.json"
            with open(log_file_name, "w") as file:
                json.dump(self.conversation_log, file, indent=4)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation log saved to {log_file_name}{Color.ENDC}\n")
            return True
        elif user_input.strip().lower() == ChatConfig.MODEL_COMMAND:
            if self.change_model():
                self.initialize_chat()
            print(f'\n')
            return True
        return False

    def change_model(self):
        """Change the AI model"""
        print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.WHITE}Current model: {Color.ENDC}{Color.PASTELPINK}{self.ai_service} - {self.gemini_model if self.ai_service == 'gemini' else self.gpt_model}{Color.ENDC}")
        change = input(f"{Color.BRIGHTYELLOW}Do you want to change the model? (yes/no): {Color.ENDC}").lower()
        if change == 'yes':
            print(f"\n{Color.BRIGHTGREEN}Available services:{Color.ENDC}")
            print(f"{Color.PASTELPINK}1. Google Gemini{Color.ENDC}")
            print(f"{Color.PASTELPINK}2. OpenAI ChatGPT{Color.ENDC}")
            service = input(f"{Color.BRIGHTYELLOW}Enter the number of the service you want to use: {Color.ENDC}")
            if service == '1':
                self.ai_service = 'gemini'
                if not self.gemini_api_key:
                    self.gemini_api_key = input("Please enter your GEMINI_API_KEY: ").strip()
                    self.initializer.gemini_api_key = self.gemini_api_key
                    ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
                try:
                    gemini_models = self.get_gemini_models()
                except Exception as e:
                    logging.error(f"Error retrieving Gemini models: {e}")
                    print(f"{Color.BRIGHTRED}Error retrieving Gemini models. Please check your API key and try again.{Color.ENDC}")
                    self.gemini_api_key = input("Please enter your GEMINI_API_KEY: ").strip()
                    self.initializer.gemini_api_key = self.gemini_api_key
                    ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
                    gemini_models = self.get_gemini_models()
                if gemini_models:
                    print(f"\n{Color.BRIGHTGREEN}Available Gemini models:{Color.ENDC}")
                    for i, model in enumerate(gemini_models, 1):
                        print(f"{Color.PASTELPINK}{i}. {model}{Color.ENDC}")
                    model_choice = input(f"{Color.BRIGHTYELLOW}Enter the number of the model you want to use: {Color.ENDC}")
                    try:
                        self.gemini_model = gemini_models[int(model_choice) - 1]
                    except (ValueError, IndexError):
                        print(f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}")
                        self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL
                else:
                    print(f"{Color.BRIGHTRED}No Gemini models available. Using default model.{Color.ENDC}")
                    self.gemini_model = ChatConfig.DEFAULT_GEMINI_MODEL
            elif service == '2':
                self.ai_service = 'openai'
                if not self.openai_api_key:
                    self.openai_api_key = input("Please enter your OPENAI_API_KEY: ").strip()
                    self.initializer.openai_api_key = self.openai_api_key
                    ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
                openai_models = self.get_openai_models()
                if openai_models:
                    print(f"\n{Color.BRIGHTGREEN}Available OpenAI models:{Color.ENDC}")
                    for i, model in enumerate(openai_models, 1):
                        print(f"{Color.PASTELPINK}{i}. {model}{Color.ENDC}")
                    model_choice = input(f"{Color.BRIGHTYELLOW}Enter the number of the model you want to use: {Color.ENDC}")
                    try:
                        self.gpt_model = openai_models[int(model_choice) - 1]
                    except (ValueError, IndexError):
                        print(f"{Color.BRIGHTRED}Invalid choice. Using default model.{Color.ENDC}")
                        self.gpt_model = ChatConfig.DEFAULT_GPT_MODEL
                else:
                    print(f"{Color.BRIGHTRED}No OpenAI models available. Using default model.{Color.ENDC}")
                    self.gpt_model = ChatConfig.DEFAULT_GPT_MODEL
            else:
                print(f"{Color.BRIGHTRED}Invalid choice. Keeping the current model.{Color.ENDC}")
                return False

            self.save_config()
            self.save_config()
            print(f"{Color.PASTELPINK}Switched to {self.ai_service.capitalize()} service. Reinitializing chat...{Color.ENDC}")
            self.chat_history = self.chat_history or []  # Ensure chat_history is not None
            self.initialize_chat()
            return True
        return False

    def process_user_input(self, chat, user_input):
        """Send user input to the language model and print the response"""
        set_stop_loading(False)
        loading_thread = threading.Thread(target=loading_animation, args=(self.loading_style,))
        loading_thread.start()

        response_text = self.send_message_to_ai(chat, user_input)

        if response_text:
            sanitized_response = remove_emojis(response_text)
            self.chat_history.append({"role": "user", "parts": [user_input]})
            self.chat_history.append({"role": "model", "parts": [sanitized_response]})
        else:
            wiki_summary = self.initializer.query_wikipedia(user_input)
            if wiki_summary:
                combined_response = combine_responses(response_text, wiki_summary)
                sanitized_response = remove_emojis(combined_response)
                self.chat_history.append({"role": "user", "parts": [user_input]})
                self.chat_history.append({"role": "model", "parts": [sanitized_response]})
            else:
                sanitized_response = f"Sorry, I couldn't find enough information on {user_input}."
                self.chat_history.append({"role": "user", "parts": [user_input]})
                self.chat_history.append({"role": "model", "parts": [sanitized_response]})

        set_stop_loading(True)
        loading_thread.join()
        sanitized_response = sanitized_response.replace('*', '')
        sanitized_response = re.sub(r'(?i)frea', '𝑓rea', sanitized_response)
        print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{sanitized_response}\n')

        """Log the conversation"""
        self.conversation_log.append(f"User: {user_input}")
        self.conversation_log.append(f"Model: {sanitized_response}")

    def send_message_to_ai(self, chat, user_input):
        """Send message to the AI service and get the response"""
        if self.ai_service == 'gemini':
            response = chat.send_message(self.instruction + user_input)
            if isinstance(response, str):
                return response
            else:
                return response.text
        elif self.ai_service == 'openai':
            messages = [{"role": "system", "content": self.instruction}]
            messages.extend([{"role": "user" if msg["role"] == "user" else "assistant", "content": msg["parts"][0]} for msg in self.chat_history])
            messages.append({"role": "user", "content": user_input})
            response = self.openai_client.chat.completions.create(
                model=self.gpt_model,
                max_tokens=1024,
                temperature=0.75,
                top_p=0.65,
                n=1,
                stop=[],
                messages=messages
            )
            return response.choices[0].message.content
        elif self.ai_service == 'langchain':
            response = chat.send_message(self.instruction + user_input)
            return response.text
        return None
    def save_config(self):
        """Save the current configuration to config.ini"""
        config = configparser.ConfigParser()
        config.read(ChatConfig.CONFIG_FILE)
        config['DEFAULT']['AIService'] = self.ai_service
        config['DEFAULT']['GeminiAPI'] = self.gemini_api_key
        config['DEFAULT']['GeminiModel'] = self.gemini_model
        config['DEFAULT']['OpenAIAPI'] = self.openai_api_key
        config['DEFAULT']['GPTModel'] = self.gpt_model
        with open(ChatConfig.CONFIG_FILE, 'w') as configfile:
            config.write(configfile)



    def initialize_chat(self):
        """Initialize the chat session"""
        logging.debug("Initializing chat session")
        self.chat_history = self.chat_history or []  # Ensure chat_history is not None
        logging.debug(f"Chat history: {self.chat_history}")
        chat = self.initializer.initialize_chat(self.chat_history)
        if chat is None:
            logging.error("Chat initialization returned None")
            logging.error("Failed to initialize chat. Exiting...")
        return chat


    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        return self.initializer.get_gemini_models()

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        return self.initializer.get_openai_models()

    def _determine_ai_service(self):
        """Determine the AI service to use based on available API keys"""
        if self.initializer.gemini_api_key:
            return 'gemini'
        elif self.initializer.openai_api_key:
            return 'openai'
        else:
            print(f"{Color.BRIGHTRED}No valid API keys found. Please provide at least one API key.{Color.ENDC}")
            self.gemini_api_key = input("Please enter your GEMINI_API_KEY (or press Enter to skip): ").strip()
            self.openai_api_key = input("Please enter your OPENAI_API_KEY (or press Enter to skip): ").strip()
            if self.gemini_api_key:
                self.initializer.gemini_api_key = self.gemini_api_key
                ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
                return 'gemini'
            elif self.openai_api_key:
                self.initializer.openai_api_key = self.openai_api_key
                ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
                return 'openai'
            else:
                raise ValueError("No valid API keys provided. Exiting...")

if __name__ == "__main__":
     chat_app = AIChat()
     chat_app.generate_chat()
