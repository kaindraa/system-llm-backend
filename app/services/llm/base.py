from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


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
