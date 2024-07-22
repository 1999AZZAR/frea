import os, readline, termios, tty, sys, threading, configparser, datetime, json, logging, time, re
from color import Color
from chat_config import ChatConfig
from terminal_utils import cursor_hide, cursor_show
from utils import remove_emojis, run_subprocess, loading_animation
import google.generativeai as genai
import openai
from openai import OpenAI




# Configure logging
logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class AIChat:
    def __init__(self):
        config = ChatConfig.initialize_config()
        self.gemini_api_key = config['DEFAULT']['GeminiAPI']
        self.openai_api_key = config['DEFAULT']['OpenAIAPI']
        self.ai_service = config['DEFAULT']['AIService']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.gpt_model = config['DEFAULT']['GPTModel']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        readline.parse_and_bind("tab: complete")
        self.conversation_log = []
        self.log_folder = ChatConfig.LOG_FOLDER
        self.chat_history = []  # Unified chat history
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def process_user_input(self):
        """Set delimiters for auto-completion and enable Vi editing mode"""
        readline.set_completer_delims(' \t\n=')
        readline.parse_and_bind("set editing-mode vi")

        try:
            """Prompt for user input"""
            question = input(f"{Color.BLUE}╭─ 𝔲ser \n╰─❯ {Color.ENDC}", end="")
        except KeyboardInterrupt:
            print("\nKeyboard Interrupt")
            return ""
        return question.strip().lower()



    def initialize_chat(self):
        """Initialize the chat session"""
        self.chat_history = self.chat_history or []  # Ensure chat_history is not None
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=self.chat_history)
        else:  # OpenAI GPT
            messages = [{"role": "system", "content": self.instruction}]
            messages.extend([{"role": "user" if msg["role"] == "user" else "assistant", "content": msg["parts"][0]} for msg in self.chat_history])
            chat = None  # We don't need to initialize a chat object for OpenAI
        self.chat_history = self.chat_history or []  # Ensure chat_history is not None
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=self.chat_history)
        else:  # OpenAI GPT
            messages = [{"role": "system", "content": self.instruction}]
            messages.extend([{"role": "user" if msg["role"] == "user" else "assistant", "content": msg["parts"][0]} for msg in self.chat_history])
            chat = None  # We don't need to initialize a chat object for OpenAI
        return chat


    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        try:
            models = genai.list_models()
            return [model.name for model in models if 'generateContent' in model.supported_generation_methods]
        except Exception as e:
            print(f"{Color.BRIGHTRED}Error retrieving Gemini models: {e}{Color.ENDC}")
            return []

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        try:
            models = self.openai_client.models.list()
            return [model.id for model in models.data if model.id.startswith("gpt")]
        except Exception as e:
            print(f"{Color.BRIGHTRED}Error retrieving OpenAI models: {e}{Color.ENDC}")
            return []

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

            # Update config file
            config = configparser.ConfigParser()
            config.read(ChatConfig.CONFIG_FILE)
            config['DEFAULT']['AIService'] = self.ai_service
            config['DEFAULT']['GeminiAPI'] = self.gemini_api_key
            config['DEFAULT']['GeminiModel'] = self.gemini_model
            config['DEFAULT']['OpenAIAPI'] = self.openai_api_key
            config['DEFAULT']['GPTModel'] = self.gpt_model
            with open(ChatConfig.CONFIG_FILE, 'w') as configfile:
                config.write(configfile)
            print(f"{Color.PASTELPINK}Switched to {self.ai_service.capitalize()} service. Reinitializing chat...{Color.ENDC}")
            self.chat_history = self.chat_history or []  # Ensure chat_history is not None
            self.initialize_chat()
            return True
        return False

    def generate_chat(self):
        """model generation response flow"""

        try:
            chat = self.initialize_chat()
            user_input = ""
            multiline_mode = False

            while True:
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

                """Handle special commands"""
                if user_input.strip().lower() == ChatConfig.EXIT_COMMAND:
                    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}\n")
                    break
                elif user_input.strip().lower() == ChatConfig.RESET_COMMAND:
                    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Resetting session...{Color.ENDC}\n")
                    time.sleep(0.5)
                    ChatConfig.clear_screen()
                    self.chat_history = []
                    chat = self.initialize_chat()
                    self.conversation_log = []
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input.strip().lower() == ChatConfig.CLEAR_COMMAND:
                    ChatConfig.clear_screen()
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input.strip().lower() == ChatConfig.HELP_COMMAND:
                    ChatConfig.display_help()
                    user_input = ""
                    multiline_mode = False
                    continue
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
                    chat = self.initialize_chat()
                    self.conversation_log = []
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input.strip().lower() == ChatConfig.PRINT_COMMAND:
                    """Save conversation log to a JSON file"""
                    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    log_file_name = f"{ChatConfig.LOG_FOLDER}/log_{current_datetime}.json"
                    with open(log_file_name, "w") as file:
                        json.dump(self.conversation_log, file, indent=4)
                    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation log saved to {log_file_name}{Color.ENDC}\n")
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input.strip().lower() == ChatConfig.MODEL_COMMAND:
                    if self.change_model():
                        chat = self.initialize_chat()
                    print(f'\n')
                    user_input = ""
                    multiline_mode = False
                    continue
                elif not user_input:
                    print(f'\n{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Please enter your command/prompt{Color.ENDC}\n')
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input.strip().lower().startswith("run "):
                    """Run a subprocess command"""
                    command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Executing 𝔲ser Command{Color.ENDC}\n')
                    run_subprocess(command)
                    user_input = ""
                    multiline_mode = False
                else:
                    """Send user input to the language model and print the response"""
                    stop_loading = False
                    loading_thread = threading.Thread(target=loading_animation, args=(self.loading_style,))
                    loading_thread.start()

                    if self.ai_service == 'gemini':
                        response = chat.send_message(self.instruction + user_input)
                        sanitized_response = remove_emojis(response.text)
                        self.chat_history.append({"role": "user", "parts": [user_input]})
                        self.chat_history.append({"role": "model", "parts": [sanitized_response]})
                    else:  # OpenAI GPT
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
                        sanitized_response = remove_emojis(response.choices[0].message.content)
                        self.chat_history.append({"role": "user", "parts": [user_input]})
                        self.chat_history.append({"role": "model", "parts": [sanitized_response]})

                    stop_loading = True
                    loading_thread.join()

                    sanitized_response = sanitized_response.replace('*', '')
                    sanitized_response = re.sub(r'(?i)frea', '𝑓rea', sanitized_response)
                    print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{sanitized_response}\n')

                    """Log the conversation"""
                    self.conversation_log.append(f"User: {user_input}")
                    self.conversation_log.append(f"Model: {sanitized_response}")

        except KeyboardInterrupt:
            print("\nKeyboard Interrupt")
            return ""

if __name__ == "__main__":
    chat_app = AIChat()
    chat_app.generate_chat()
