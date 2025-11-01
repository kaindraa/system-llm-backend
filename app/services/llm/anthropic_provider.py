from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.services.llm.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic provider implementation using langchain-anthropic.
    Uses endpoint: https://api.anthropic.com/v1/messages
    Supports all Anthropic models including Claude 3, Claude 3.5, etc.
    """

    def __init__(
        self,
        model_name: str = "claude-3-haiku-20240307",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Anthropic provider.

        Args:
            model_name: Anthropic model name (e.g., 'claude-3-haiku-20240307', 'claude-3-opus-20240229')
            api_key: Anthropic API key (if None, will use ANTHROPIC_API_KEY env var)
            **kwargs: Additional configuration passed to ChatAnthropic
        """
        super().__init__(model_name, **kwargs)

        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

        # Initialize ChatAnthropic client
        self._client = self._create_client()

    def _create_client(self) -> ChatAnthropic:
        """
        Create ChatAnthropic client.
        """
        client_config = {
            "model": self.model_name,
            "temperature": 1,  # Use default temperature
        }

        # Add API key if provided
        if self.api_key:
            client_config["api_key"] = self.api_key

        return ChatAnthropic(**client_config)

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
        Generate response from Anthropic model (synchronous).

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
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    async def agenerate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from Anthropic model (asynchronous).

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
            raise RuntimeError(f"Anthropic API error: {str(e)}")

    async def agenerate_stream(self, messages: List[Dict[str, str]]):
        """
        Generate streaming response from Anthropic model (asynchronous).
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
            raise RuntimeError(f"Anthropic API streaming error: {str(e)}")

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "anthropic"

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        info = super().get_model_info()
        info.update({
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
        })
        return info
