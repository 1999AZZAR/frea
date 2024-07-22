import os, subprocess, time, re, readline, termios, tty, sys, threading, configparser, datetime, json, logging
from color import Color
from terminal_utils import cursor_hide, cursor_show
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

    def remove_emojis(self, text):
        """Remove emojis from the model response"""
        emoji_pattern = re.compile("["
                                    u"\U0001F600-\U0001F64F"
                                    u"\U0001F300-\U0001F5FF"
                                    u"\U0001F680-\U0001F6FF"
                                    u"\U0001F1E0-\U0001F1FF"
                                    u"\U00002500-\U00002BEF"
                                    u"\U00002702-\U000027B0"
                                    u"\U00002702-\U000027B0"
                                    u"\U000024C2-\U0001F251"
                                    u"\U0001f926-\U0001f937"
                                    u"\U00010000-\U0010ffff"
                                    u"\u2640-\u2642"
                                    u"\u2600-\u2B55"
                                    u"\u200d"
                                    u"\u23cf"
                                    u"\u23e9"
                                    u"\u231a"
                                    u"\ufe0f"
                                    u"\u3030"
                                   "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def run_subprocess(self, command):
        """Run a subprocess command"""
        try:
            subprocess.run(command, shell=True)
        except Exception as e:
            """error handling"""
            print(f"{Color.BRIGHTYELLOW}\n╰─❯ {Color.ENDC}{Color.BRIGHTRED}subprocess execution error: {e}{Color.ENDC}")

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
        @staticmethod
        def loading_animation(use='L2'):
            """loading animation"""
            cursor_hide()
            while not stop_loading:
                animations = {
                    'L0': ([' 🙉 ', ' 🙈 ', ' 🙊 ', ' 🙈 '], 0.2),
                    'L1': ([' ∙∙∙∙∙ ', ' ●∙∙∙∙ ', ' ∙●∙∙∙ ', ' ∙∙●∙∙ ', ' ∙∙∙●∙ ', ' ∙∙∙∙● '], 0.1),
                    'L2': ([' ⣾ ', ' ⣽ ', ' ⣻ ', ' ⢿ ', ' ⡿ ', ' ⣟ ', ' ⣯ ', ' ⣷ '], 0.15),
                    'L3': ([' 🌑 ', ' 🌒 ', ' 🌓 ', ' 🌔 ', ' 🌕 ', ' 🌖 ', ' 🌗 ', ' 🌘 '], 0.22),
                    'L4': ([' ◐ ', ' ◓ ', ' ◑ ', ' ◒ '], 0.1),
                    'L5': ([' ▖ ', ' ▘ ', ' ▝ ', ' ▗ '], 0.2),
                    'L6': ([' ⠁ ', ' ⠂ ', ' ⠄ ', ' ⡀ ', ' ⢀ ', ' ⠠ ', ' ⠐ ', ' ⠈ '], 0.15),
                    'L7': ([' ⣀ ', ' ⣤ ', ' ⣶ ', ' ⣾ ', ' ⣿ ', ' ⣷ ', ' ⣯ ', ' ⣟ '], 0.2),
                    'L8': ([' 🕛 ', ' 🕐 ', ' 🕑 ', ' 🕒 ', ' 🕓 ', ' 🕔 ', ' 🕕 ', ' 🕖 ', ' 🕗 ', ' 🕘 ', ' 🕙 ', ' 🕚 '], 0.15),
                    'L9': ([' 🔸 ', ' 🔹 ', ' 🔷 ', ' 🔶 '], 0.2),
                    'L10': ([' .    ',' ..   ',' ...  ',' .... '], 0.15)
                }
                if use in animations:
                    frames, delay = animations[use]
                    for frame in frames:
                        print(f"{Color.LIGHTPURPLE}\r{frame}Processing{Color.ENDC}", end="")
                        time.sleep(delay)
            cursor_show()
            print("\r" + " " * 20 + "\r", end="")

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
                if user_input == ChatConfig.EXIT_COMMAND:
                    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}\n")
                    break
                elif user_input == ChatConfig.RESET_COMMAND:
                    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Resetting session...{Color.ENDC}\n")
                    time.sleep(0.5)
                    ChatConfig.clear_screen()
                    self.chat_history = []
                    chat = self.initialize_chat()
                    self.conversation_log = []
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == ChatConfig.CLEAR_COMMAND:
                    ChatConfig.clear_screen()
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == ChatConfig.HELP_COMMAND:
                    ChatConfig.display_help()
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == ChatConfig.RECONFIGURE_COMMAND:
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
                elif user_input == ChatConfig.PRINT_COMMAND:
                    """Save conversation log to a JSON file"""
                    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    log_file_name = f"{ChatConfig.LOG_FOLDER}/log_{current_datetime}.json"
                    with open(log_file_name, "w") as file:
                        json.dump(self.conversation_log, file, indent=4)
                    print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.PASTELPINK}Conversation log saved to {log_file_name}{Color.ENDC}\n")
                    user_input = ""
                    multiline_mode = False
                    continue
                elif user_input == ChatConfig.MODEL_COMMAND:
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
                elif user_input.startswith("run "):
                    """Run a subprocess command"""
                    command = user_input[4:].strip()
                    print(f'{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Executing 𝔲ser Command{Color.ENDC}\n')
                    self.run_subprocess(command)
                    user_input = ""
                    multiline_mode = False
                else:
                    """Send user input to the language model and print the response"""
                    stop_loading = False
                    loading_thread = threading.Thread(target=loading_animation, args=(self.loading_style,))
                    loading_thread.start()

                    if self.ai_service == 'gemini':
                        response = chat.send_message(self.instruction + user_input)
                        sanitized_response = self.remove_emojis(response.text)
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
                        sanitized_response = self.remove_emojis(response.choices[0].message.content)
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

                user_input = ""
                multiline_mode = False

        except KeyboardInterrupt:
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}\n")

        except KeyboardInterrupt:
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.LIGHTRED}Exiting.... Goodbye!{Color.ENDC}\n")
        except ValueError as ve:
            logging.error("ValueError: %s", ve)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.BRIGHTRED}A value error occurred: {ve}{Color.ENDC}\n")
        except configparser.Error as ce:
            logging.error("ConfigParser Error: %s", ce)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.BRIGHTRED}Configuration error occurred. Entering configuration mode...{Color.ENDC}\n")
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
        except subprocess.CalledProcessError as spe:
            logging.error("Subprocess Error: %s", spe)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.BRIGHTRED}Subprocess error: {spe}{Color.ENDC}\n")
        except genai.exceptions.InvalidAPIKeyError as e:
            logging.error("Invalid Gemini API Key: %s", e)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.BRIGHTRED}Invalid Gemini API Key. Please enter a new key.{Color.ENDC}\n")
            self.gemini_api_key = input("Enter the new Gemini API key: ")
            ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
            chat = self.initialize_chat()
        except openai.error.AuthenticationError as e:
            logging.error("Invalid OpenAI API Key: %s", e)
            print(f"{Color.BRIGHTYELLOW}\n╭─ 𝑓rea \n╰─❯ {Color.ENDC}{Color.BRIGHTRED}Invalid OpenAI API Key. Please enter a new key.{Color.ENDC}\n")
            self.openai_api_key = input("Enter the new OpenAI API key: ")
            ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            chat = self.initialize_chat()
        finally:
            stop_loading = True

if __name__ == "__main__":
    chat_app = AIChat()
    chat_app.generate_chat()
