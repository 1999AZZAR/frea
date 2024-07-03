import os
import configparser
import logging
import google.generativeai as genai
from chat_config import ChatConfig
import wikipediaapi

class ChatInitializer:
    def __init__(self):
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', config['DEFAULT']['GeminiAPI'])
        self.gemini_model = config['DEFAULT']['GeminiModel']
        self.loading_style = config['DEFAULT']['LoadingStyle']
        self.ai_service = config['DEFAULT']['AIService']
        ChatConfig.initialize_apis(self.gemini_api_key)
        self.instruction_file = config['DEFAULT']['InstructionFile']
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """Initialize the chat session"""
        if self.ai_service == 'gemini':
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings
            )
            chat = model.start_chat(history=chat_history)
        return chat

    def get_gemini_models(self):
        """Retrieve available Gemini models"""
        models = genai.list_models()
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]

    def query_wikipedia(self, query):
        """Query Wikipedia for additional information"""
        user_agent = "frea/1.0 (azzarmrzs@gmail.com)"
        wiki_wiki = wikipediaapi.Wikipedia(language='en', user_agent=user_agent)
        page = wiki_wiki.page(query)
        if page.exists():
            summary_paragraphs = page.summary.split('\n')
            summary = '\n'.join(summary_paragraphs[:5])
            link = page.fullurl
            return f"{summary}\n\nFor more information, visit: {link}"
        else:
            return None
