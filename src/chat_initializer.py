import os
import openai
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
        self.groq_api_key = os.getenv("GROQ_API_KEY", config["DEFAULT"]["GroqAPI"])
        self.ai_service = config["DEFAULT"]["AIService"]
        self.model = config["DEFAULT"]["AIModel"]
        self.loading_style = config["DEFAULT"]["LoadingStyle"]
        self.instruction_file = config["DEFAULT"]["InstructionFile"]
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

        # Initialize the OpenAI client based on the AI service
        if self.ai_service == "gemini":
            self.client = openai.OpenAI(
                api_key=self.gemini_api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
        elif self.ai_service == "groq":
            self.client = openai.OpenAI(
                api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1"
            )
        else:
            raise ValueError(f"Unsupported AI service: {self.ai_service}")

    def initialize_chat(self, chat_history):
        """
        Initializes the chat session with the specified chat history.

        Args:
            chat_history (list): The chat history to initialize the session with.

        Returns:
            Chat: The initialized chat session.
        """
        return chat_history  # Return the chat history as the "chat" object

    def get_models(self):
        """
        Retrieves available models for the current AI service.

        Returns:
            list: A list of available model names.
        """
        if self.ai_service == "gemini":
            return [
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-2.0-flash-exp",
                "gemini-2.0-flash-thinking-exp-01-21",
            ]
        elif self.ai_service == "groq":
            return [
                "llama3-8b-8192",
                "llama3-70b-8192",
                "gemma2-9b-it",
                "mixtral-8x7b-32768",
                "deepseek-r1-distill-llama-70b",
                "llama-3.3-70b-specdec",
            ]
        else:
            return []

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
