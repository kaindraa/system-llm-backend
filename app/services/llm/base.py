from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.tools import Tool


class BaseLLMProvider(ABC):
    """
    Base abstract class for LLM providers.
    This allows easy switching between different LLM providers (OpenAI, Ollama, etc.)
    """

    def __init__(self, model_name: str, **kwargs):
        """
        Initialize LLM provider with model name and additional configuration.

        Args:
            model_name: Name of the model to use
            **kwargs: Additional provider-specific configuration
        """
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from LLM using provider defaults.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def agenerate(self, messages: List[Dict[str, str]]) -> str:
        """
        Async version of generate using provider defaults.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the provider.

        Returns:
            Provider name (e.g., 'openai', 'ollama', 'anthropic')
        """
        pass

    async def agenerate_stream_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Tool],
        max_iterations: int = 10
    ):
        """
        Generate streaming response with tool calling support.

        Yields chunks of the final response after executing any tool calls.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: List of Langchain Tool objects available for the LLM to call
            max_iterations: Maximum number of tool call iterations (to prevent infinite loops)

        Yields:
            Dict with response data:
            - 'type': 'chunk' for text chunks, 'tool_call' for tool calls, 'tool_result' for tool results
            - 'content': The actual content
        """
        raise NotImplementedError(
            f"Tool calling not yet implemented for {self.get_provider_name()} provider. "
            "Override this method in the provider implementation."
        )

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.

        Returns:
            Dictionary with model information
        """
        return {
            "provider": self.get_provider_name(),
            "model_name": self.model_name,
            "config": self.config
        }
