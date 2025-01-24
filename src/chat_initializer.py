import os
import google.generativeai as genai
from chat_config import ChatConfig
import wikipediaapi


class ChatInitializer:
    USER_AGENT = "frea/1.0 (azzarmrzs@gmail.com)"

    def __init__(self):
        """
        Initializes the chat session by loading configuration and setting up APIs.
        """
        config = ChatConfig.initialize_config()
        if not config:
            raise ValueError("Configuration initialization failed")

        self.gemini_api_key = os.getenv(
            "GEMINI_API_KEY", config["DEFAULT"]["GeminiAPI"]
        )
        self.gemini_model = config["DEFAULT"]["GeminiModel"]
        self.loading_style = config["DEFAULT"]["LoadingStyle"]
        self.ai_service = config["DEFAULT"]["AIService"]
        ChatConfig.initialize_apis(self.gemini_api_key)
        self.instruction_file = config["DEFAULT"]["InstructionFile"]
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

    def initialize_chat(self, chat_history):
        """
        Initializes the chat session with the specified chat history.

        Args:
            chat_history (list): The chat history to initialize the session with.

        Returns:
            Chat: The initialized chat session.
        """
        if self.ai_service == "gemini":
            generation_config = ChatConfig.gemini_generation_config()
            safety_settings = ChatConfig.gemini_safety_settings()
            model = genai.GenerativeModel(
                generation_config=generation_config,
                model_name=self.gemini_model,
                safety_settings=safety_settings,
            )
            chat = model.start_chat(history=chat_history)
            return chat
        return None

    def get_gemini_models(self):
        """
        Retrieves available Gemini models.

        Returns:
            list: A list of available Gemini model names.
        """
        models = genai.list_models()
        return [
            model.name
            for model in models
            if "generateContent" in model.supported_generation_methods
        ]

    def query_wikipedia(self, query):
        """
        Queries Wikipedia for additional information.

        Args:
            query (str): The query to search for on Wikipedia.

        Returns:
            str: A summary of the Wikipedia page, or None if the page does not exist.
        """
        wiki_wiki = wikipediaapi.Wikipedia(language="en", user_agent=self.USER_AGENT)
        page = wiki_wiki.page(query)
        if page.exists():
            summary_paragraphs = page.summary.split("\n")
            summary = "\n".join(summary_paragraphs[:3])
            link = page.fullurl
            return f"{summary}\nFor more information, visit: {link}"
        return None
