import os
import openai
from chat_config import ChatConfig
import wikipediaapi
from functools import lru_cache
import re

# Import potential exceptions from openai library for more specific handling
from openai import APIConnectionError, AuthenticationError, RateLimitError
import warnings  # To warn if the configured model isn't available


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
        # Store the model name from config initially
        self.configured_model = config["DEFAULT"]["AIModel"]
        self.loading_style = config["DEFAULT"]["LoadingStyle"]
        self.instruction_file = config["DEFAULT"]["InstructionFile"]
        self.instruction = ChatConfig.chat_instruction(self.instruction_file)

        # Initialize the OpenAI client based on the AI service
        self.client = None  # Initialize client to None first
        try:
            if self.ai_service == "gemini":
                # Note: Using the OpenAI SDK with Google's endpoint.
                # Model listing (`client.models.list()`) compatibility depends on Google's implementation.
                # If this fails, using the native 'google-generativeai' SDK might be necessary for model listing.
                self.client = openai.OpenAI(
                    api_key=self.gemini_api_key,
                    # The base URL provided in the original code. Double-check if this is the correct one
                    # for OpenAI SDK compatibility, especially for model listing.
                    # Sometimes it might just be "https://generativelanguage.googleapis.com/v1beta"
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                )
            elif self.ai_service == "groq":
                self.client = openai.OpenAI(
                    api_key=self.groq_api_key, base_url="https://api.groq.com/openai/v1"
                )
            else:
                # Keep the original ValueError for unsupported service
                raise ValueError(f"Unsupported AI service: {self.ai_service}")

            # Assign the configured model name to the instance variable 'model'
            self.model = self.configured_model

        # Catch specific API errors during initialization if possible
        except AuthenticationError as e:
            print(
                f"Authentication Error initializing API client for {self.ai_service}: {e}. Check API Key."
            )
            raise ConnectionError(f"Authentication failed for {self.ai_service}") from e
        except APIConnectionError as e:
            print(
                f"Connection Error initializing API client for {self.ai_service}: {e}. Check API endpoint and network."
            )
            raise ConnectionError(f"Could not connect to {self.ai_service} API") from e
        except Exception as e:
            # Catch any other unexpected error during initialization
            print(
                f"An unexpected error occurred during client initialization for {self.ai_service}: {e}"
            )
            # Decide if you want to raise here or handle differently (e.g., allow running without a client)
            raise RuntimeError(f"Failed to initialize AI client: {e}") from e

        # Optional: Verify the configured model exists upon initialization
        # available_models = self.get_models() # Fetch models right away
        # if available_models and self.model not in available_models:
        #      warnings.warn(
        #          f"Configured model '{self.model}' not found in available models for {self.ai_service}. "
        #          f"Available: {available_models}. Using configured model anyway."
        #      )

    def initialize_chat(self, chat_history):
        """
        Initializes the chat session with the specified chat history.

        Args:
            chat_history (list): The chat history to initialize the session with.

        Returns:
            list: The initialized chat history.
        """
        # The original function just returned the history, keeping that behavior.
        # If actual initialization logic is needed (like adding system prompt), do it here.
        # Example:
        # initial_prompt = {"role": "system", "content": self.instruction}
        # return [initial_prompt] + chat_history if chat_history else [initial_prompt]
        return chat_history

    def get_models(self):
        """
        Retrieves available models dynamically from the configured AI service API.

        Returns:
            list: A sorted list of available model names (strings),
                  or an empty list if retrieval fails or client is not initialized.
        """
        if not self.client:
            print("Warning: AI client is not initialized. Cannot fetch models.")
            return []

        try:
            # Use the standard OpenAI client method to list models
            models_response = self.client.models.list()

            # The response is typically an iterable (like openai.pagination.SyncPage)
            # containing model objects, each having an 'id' attribute.
            model_ids = [model.id for model in models_response if hasattr(model, "id")]

            # Filter specific model types if necessary (example for Gemini if needed)
            # if self.ai_service == "gemini":
            #    model_ids = [m for m in model_ids if m.startswith('gemini-')] # Or other filtering logic

            return sorted(model_ids)  # Return sorted list for consistency

        except AuthenticationError:
            print(
                f"Authentication Error: Failed to fetch models for {self.ai_service}. Check your API key."
            )
            return []
        except APIConnectionError:
            print(
                f"Connection Error: Could not connect to {self.ai_service} API to fetch models."
            )
            return []
        except RateLimitError:
            print(
                f"Rate Limit Error: Exceeded API rate limit for {self.ai_service} when fetching models."
            )
            return []
        except Exception as e:
            # Catch other potential errors (e.g., endpoint not supporting models.list(), unexpected response format)
            print(f"An error occurred while fetching models for {self.ai_service}: {e}")
            # Returning an empty list signifies failure to retrieve models
            return []

    @lru_cache(maxsize=32)
    def query_wikipedia(self, query, sentences=3):
        """
        Queries Wikipedia for additional information.

        Args:
            query (str): The query to search for on Wikipedia.
            sentences (int): Number of sentences to return in the summary.

        Returns:
            str: A concise summary limited to `sentences`, or None if page not found.
        """
        wiki_wiki = wikipediaapi.Wikipedia(language="en", user_agent=self.USER_AGENT)
        page = wiki_wiki.page(query)
        if not page.exists():
            return None
        summary = page.summary or ""
        # Split into sentences and limit
        sentences_list = re.split(r'(?<=[\.!?]) +', summary)
        selected = sentences_list[:sentences]
        result = " ".join(selected).strip()
        return f"{result}\n\nRead more: {page.fullurl}"
