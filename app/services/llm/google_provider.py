from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.services.llm.base import BaseLLMProvider


class GoogleProvider(BaseLLMProvider):
    """
    Google Generative AI provider implementation using langchain-google-genai.
    Uses endpoint: https://generativelanguage.googleapis.com/v1beta/models/
    Supports all Google Gemini models including Gemini 2.5, Gemini 2.0, etc.
    """

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Google Generative AI provider.

        Args:
            model_name: Google model name (e.g., 'gemini-2.0-flash', 'gemini-1.5-pro')
            api_key: Google API key (if None, will use GOOGLE_API_KEY env var)
            **kwargs: Additional configuration passed to ChatGoogleGenerativeAI
        """
        super().__init__(model_name, **kwargs)

        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/"

        # Initialize ChatGoogleGenerativeAI client
        self._client = self._create_client()

    def _create_client(self) -> ChatGoogleGenerativeAI:
        """
        Create ChatGoogleGenerativeAI client.
        """
        client_config = {
            "model": self.model_name,
            "temperature": 1,  # Use default temperature
        }

        # Add API key if provided
        # NOTE: Parameter name is google_api_key (not api_key)
        if self.api_key:
            client_config["google_api_key"] = self.api_key

        return ChatGoogleGenerativeAI(**client_config)

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """
        Convert message dictionaries to langchain message objects.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            List of langchain message objects
        """
        langchain_messages = []

        for msg in messages:
            role = msg.get("role", "user").lower()
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # default to user
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from Google Gemini model (synchronous).

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        try:
            # Generate response
            response = self._client.invoke(langchain_messages)
            return response.content
        except Exception as e:
            raise RuntimeError(f"Google Generative AI error: {str(e)}")

    async def agenerate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from Google Gemini model (asynchronous).

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        try:
            # Generate response asynchronously
            response = await self._client.ainvoke(langchain_messages)
            return response.content
        except Exception as e:
            raise RuntimeError(f"Google Generative AI error: {str(e)}")

    async def agenerate_stream(self, messages: List[Dict[str, str]]):
        """
        Generate streaming response from Google Gemini model (asynchronous).
        Yields chunks of text as they are generated.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Yields:
            str: Text chunks as they are generated
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        try:
            # Stream response asynchronously
            async for chunk in self._client.astream(langchain_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            raise RuntimeError(f"Google Generative AI streaming error: {str(e)}")

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "google"

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        info = super().get_model_info()
        info.update({
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
        })
        return info
