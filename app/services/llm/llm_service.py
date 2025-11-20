from typing import Dict, Any, Optional, Type, List
from sqlalchemy.orm import Session
from langchain_core.tools import Tool
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.google_provider import GoogleProvider
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.models.model import Model
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class LLMService:
    """
    Service for managing LLM providers and switching between models.
    This service acts as a factory and manager for different LLM providers.
    """

    # Registry of available providers
    PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "openrouter": OpenRouterProvider,
        # Future providers can be added here:
        # "ollama": OllamaProvider,
        # "huggingface": HuggingFaceProvider,
    }

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize LLM service.

        Args:
            db: Database session for fetching model configurations
        """
        self.db = db
        self._providers: Dict[str, BaseLLMProvider] = {}

    def get_provider(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Get or create a provider for the specified model.

        Args:
            model_id: Model ID (UUID) or model name from database
            api_key: API key for the provider (if required)
            **kwargs: Additional provider-specific configuration

        Returns:
            Initialized LLM provider

        Raises:
            ValueError: If model not found or provider not supported
        """
        # Check if provider already exists in cache
        if model_id in self._providers:
            return self._providers[model_id]

        # Fetch model from database
        if self.db:
            model = self._get_model_from_db(model_id)
            if not model:
                raise ValueError(f"Model with ID '{model_id}' not found in database")

            provider_name = model.provider.lower()
            model_name = model.name
            api_endpoint = model.api_endpoint
        else:
            # If no database, assume direct provider configuration
            # Format: "provider:model_name"
            if ":" in model_id:
                provider_name, model_name = model_id.split(":", 1)
                api_endpoint = None
            else:
                raise ValueError(
                    "Invalid model_id format. Use 'provider:model_name' or provide database session"
                )

        # Get provider class from registry
        provider_class = self.PROVIDER_REGISTRY.get(provider_name)
        if not provider_class:
            raise ValueError(
                f"Provider '{provider_name}' not supported. "
                f"Available providers: {list(self.PROVIDER_REGISTRY.keys())}"
            )

        # Create provider instance
        provider_kwargs = kwargs.copy()

        # Get API key from parameter or settings
        if api_key:
            provider_kwargs["api_key"] = api_key
        else:
            # Try to get API key from config settings
            api_key_config = {
                "openai": settings.OPENAI_API_KEY,
                "anthropic": settings.ANTHROPIC_API_KEY,
                "google": settings.GOOGLE_API_KEY,
                "openrouter": settings.OPENROUTER_API_KEY,
            }
            config_key = api_key_config.get(provider_name)
            if config_key:
                provider_kwargs["api_key"] = config_key

        # For OpenAI, don't pass base_url as langchain handles it
        # For other providers, pass custom endpoints
        if api_endpoint and provider_name != "openai":
            provider_kwargs["base_url"] = api_endpoint

        provider = provider_class(model_name=model_name, **provider_kwargs)

        # Cache provider
        self._providers[model_id] = provider

        logger.info(
            f"Initialized LLM provider: {provider_name} with model: {model_name}"
        )

        return provider

    def _get_model_from_db(self, model_id: str) -> Optional[Model]:
        """
        Fetch model from database by ID or name.

        Args:
            model_id: Model UUID or name

        Returns:
            Model object or None
        """
        if not self.db:
            return None

        # Try to fetch by ID first
        try:
            from uuid import UUID
            uuid_obj = UUID(model_id)
            model = self.db.query(Model).filter(Model.id == uuid_obj).first()
            if model:
                return model
        except (ValueError, AttributeError):
            pass

        # Try to fetch by name
        model = self.db.query(Model).filter(Model.name == model_id).first()
        return model

    async def generate_async(
        self,
        model_id: str,
        messages: list[Dict[str, str]],
        api_key: Optional[str] = None
    ) -> str:
        """
        Generate response using specified model (async).
        Uses provider defaults.

        Args:
            model_id: Model ID or name
            messages: List of message dictionaries
            api_key: API key for provider

        Returns:
            Generated text response
        """
        provider = self.get_provider(model_id, api_key=api_key)
        response = await provider.agenerate(messages=messages)
        return response

    async def generate_stream(
        self,
        model_id: str,
        messages: list[Dict[str, str]],
        api_key: Optional[str] = None
    ):
        """
        Generate streaming response using specified model (async).
        Yields chunks of text as they are generated.

        Args:
            model_id: Model ID or name
            messages: List of message dictionaries
            api_key: API key for provider

        Yields:
            str: Text chunks as they are generated
        """
        provider = self.get_provider(model_id, api_key=api_key)
        async for chunk in provider.agenerate_stream(messages=messages):
            yield chunk

    def generate_sync(
        self,
        model_id: str,
        messages: list[Dict[str, str]],
        api_key: Optional[str] = None
    ) -> str:
        """
        Generate response using specified model (sync).
        Uses provider defaults.

        Args:
            model_id: Model ID or name
            messages: List of message dictionaries
            api_key: API key for provider

        Returns:
            Generated text response
        """
        provider = self.get_provider(model_id, api_key=api_key)
        response = provider.generate(messages=messages)
        return response

    def get_available_providers(self) -> list[str]:
        """
        Get list of available provider names.

        Returns:
            List of provider names
        """
        return list(self.PROVIDER_REGISTRY.keys())

    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model_id: Model ID or name

        Returns:
            Dictionary with model information
        """
        provider = self.get_provider(model_id)
        return provider.get_model_info()

    def clear_cache(self):
        """Clear the provider cache."""
        self._providers.clear()
        logger.info("LLM provider cache cleared")

    async def stream_response_with_tools(
        self,
        model_id: str,
        messages: list[Dict[str, str]],
        tools: List[Tool],
        api_key: Optional[str] = None,
        max_iterations: int = 10
    ):
        """
        Stream response using specified model with tool calling support.

        Allows the LLM to call tools (like semantic search) to augment its response.

        Args:
            model_id: Model ID or name
            messages: List of message dictionaries
            tools: List of Langchain Tool objects
            api_key: API key for provider
            max_iterations: Maximum tool calling iterations

        Yields:
            Dict with event data from tool calling loop
        """
        provider = self.get_provider(model_id, api_key=api_key)
        async for event in provider.agenerate_stream_with_tools(
            messages=messages,
            tools=tools,
            max_iterations=max_iterations
        ):
            yield event
