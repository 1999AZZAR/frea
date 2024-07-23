import os
import configparser
import logging
import google.generativeai as genai
import openai
from openai import OpenAI
from chat_config import ChatConfig
import wikipediaapi
from langchain_openai import ChatOpenAI

def initialize_chat(self, chat_history):
    """Initialize the chat session"""
    logging.debug(f"AI Service: {self.ai_service}")
    if self.ai_service == 'gemini':
        generation_config = ChatConfig.gemini_generation_config()
        safety_settings = ChatConfig.gemini_safety_settings()
        model = genai.GenerativeModel(
            generation_config=generation_config,
            model_name=self.gemini_model,
            safety_settings=safety_settings
        )
        chat = model.start_chat(history=chat_history)
    elif self.ai_service == 'langchain':
        chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
    elif self.ai_service == 'openai':
        chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
    else:
        logging.error(f"Unsupported AI service: {self.ai_service}")
        chat = None
    return chat

def get_gemini_models(self):
    """Retrieve available Gemini models"""
    models = genai.list_models()
    return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

def get_openai_models(self):
    """Retrieve available OpenAI models"""
    models = self.openai_client.models.list()
    return [model.id for model in models.data if model.id.startswith("gpt")]
class ChatInitializer:
    def __init__(self):
        self._initialize_config()
        self._initialize_clients()

    def _initialize_config(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def _initialize_clients(self):
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)

    def _get_api_key(self, env_var, default_key):
        api_key = os.getenv(env_var, default_key)
        return api_key
    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            return self._initialize_gemini_chat(chat_history)
        elif self.ai_service == 'langchain':
            return self._initialize_langchain_chat(chat_history)
        elif self.ai_service == 'openai':
            return self._initialize_openai_chat(chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            return None

    def _initialize_gemini_chat(self, chat_history):
        generation_config = ChatConfig.gemini_generation_config()
        safety_settings = ChatConfig.gemini_safety_settings()
        model = genai.GenerativeModel(
            generation_config=generation_config,
            model_name=self.gemini_model,
            safety_settings=safety_settings
        )
        return model.start_chat(history=chat_history)

    def _initialize_langchain_chat(self, chat_history):
        return LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)

    def _initialize_openai_chat(self, chat_history):
        return OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        models = self.openai_client.models.list()
        return [model.id for model in models.data if model.id.startswith("gpt")]
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        elif self.ai_service == 'langchain':
            chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
        elif self.ai_service == 'openai':
            chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            chat = None
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        models = self.openai_client.models.list()
        return [model.id for model in models.data if model.id.startswith("gpt")]
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        elif self.ai_service == 'langchain':
            chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
        elif self.ai_service == 'openai':
            chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            chat = None
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        models = self.openai_client.models.list()
        return [model.id for model in models.data if model.id.startswith("gpt")]
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        elif self.ai_service == 'langchain':
            chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
        elif self.ai_service == 'openai':
            chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            chat = None
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        models = self.openai_client.models.list()
        return [model.id for model in models.data if model.id.startswith("gpt")]
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        elif self.ai_service == 'langchain':
            chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
        elif self.ai_service == 'openai':
            chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            chat = None
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        models = self.openai_client.models.list()
        return [model.id for model in models.data if model.id.startswith("gpt")]
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        elif self.ai_service == 'langchain':
            chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
        elif self.ai_service == 'openai':
            chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            chat = None
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def get_openai_models(self):
        """Retrieve available OpenAI models"""
        models = self.openai_client.models.list()
        return [model.id for model in models.data if model.id.startswith("gpt")]
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        logging.debug(f"AI Service: {self.ai_service}")
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        elif self.ai_service == 'langchain':
            chat = LangChainChat(self.langchain_client, self.gpt_model, self.instruction, chat_history)
        elif self.ai_service == 'openai':
            chat = OpenAIChat(self.openai_client, self.gpt_model, self.instruction, chat_history)
        else:
            logging.error(f"Unsupported AI service: {self.ai_service}")
            chat = None
        return chat
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.openai_api_key = os.getenv('OPENAI_API_KEY', config['DEFAULT']['OpenAIAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.gpt_model = config['DEFAULT']['GPTModel']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key, self.openai_api_key)
        self.langchain_client = ChatOpenAI(api_key=self.openai_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def query_wikipedia(self, query):
        """Query Wikipedia for additional information"""
        page = self.wiki_wiki.page(query)
        if page.exists():
            return page.summary
        else:
            return None
class OpenAIChat:
    def __init__(self, client, model, instruction, chat_history):
        self.client = client
        self.model = model
        self.instruction = instruction
        self.chat_history = chat_history

    def send_message(self, user_input):
        messages = [{"role": "system", "content": self.instruction}]
        messages.extend([{"role": "user" if msg["role"] == "user" else "assistant", "content": msg["parts"][0]} for msg in self.chat_history])
        messages.append({"role": "user", "content": user_input})
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.75,
            top_p=0.65,
            n=1,
            stop=[],
            messages=messages
        )
        return response.choices[0].message.content

class LangChainChat:
    def __init__(self, client, model, instruction, chat_history):
        self.client = client
        self.model = model
        self.instruction = instruction
        self.chat_history = chat_history

    def send_message(self, user_input):
        messages = [{"role": "system", "content": self.instruction}]
        messages.extend([{"role": "user" if msg["role"] == "user" else "assistant", "content": msg["parts"][0]} for msg in self.chat_history])
        messages.append({"role": "user", "content": user_input})
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.75,
            top_p=0.65,
            n=1,
            stop=[],
            messages=messages
        )
        return response.choices[0].message.content
