from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.services.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation using langchain-openai.
    Uses endpoint: https://api.openai.com/v1/chat/completions
    Supports all OpenAI models including GPT-5, GPT-4.1, GPT-4o, etc.
    """

    def __init__(
        self,
        model_name: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI provider.

        Args:
            model_name: OpenAI model name (e.g., 'gpt-5-mini', 'gpt-4.1', 'gpt-4o')
            api_key: OpenAI API key (if None, will use OPENAI_API_KEY env var)
            **kwargs: Additional configuration passed to ChatOpenAI
        """
        super().__init__(model_name, **kwargs)

        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

        # Initialize ChatOpenAI client
        self._client = self._create_client()

    def _create_client(self) -> ChatOpenAI:
        """
        Create ChatOpenAI client.
        IMPORTANT: langchain-openai has default temperature=0.7
        We need to NOT pass it to OpenAI API to let model use its own default.
        We can't unset it in langchain, so we just don't include it in model_kwargs.
        """
        client_config = {
            "model": self.model_name,
            # Explicitly empty model_kwargs to prevent any extra params
            "model_kwargs": {},
            "temperature": 1

        }

        # Add API key if provided
        if self.api_key:
            client_config["api_key"] = self.api_key

        # Only add base_url if it's custom (not default OpenAI)
        if self.base_url and self.base_url != "https://api.openai.com/v1":
            client_config["base_url"] = self.base_url

        return ChatOpenAI(**client_config)

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
        Generate response from OpenAI model (synchronous) using provider defaults.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        # Temporarily remove temperature to avoid sending it to API
        # langchain has default temperature=0.7 which gpt-5-mini doesn't support
        original_temp = self._client.temperature
        original_max_tokens = self._client.max_tokens

        # Unset them (will not be sent to API)
        self._client.temperature = 1
        self._client.max_tokens = None

        try:
            # Generate response with model defaults
            response = self._client.invoke(langchain_messages)
            return response.content
        finally:
            # Restore original values
            self._client.temperature = original_temp
            self._client.max_tokens = original_max_tokens

    async def agenerate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from OpenAI model (asynchronous) using provider defaults.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        # Temporarily remove temperature to avoid sending it to API
        # langchain has default temperature=0.7 which gpt-5-mini doesn't support
        original_temp = self._client.temperature
        original_max_tokens = self._client.max_tokens

        # Unset them (will not be sent to API)
        self._client.temperature = 1
        self._client.max_tokens = None

        try:
            # Generate response asynchronously with model defaults
            response = await self._client.ainvoke(langchain_messages)
            return response.content
        finally:
            # Restore original values
            self._client.temperature = original_temp
            self._client.max_tokens = original_max_tokens

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        info = super().get_model_info()
        info.update({
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
        })
        return info
