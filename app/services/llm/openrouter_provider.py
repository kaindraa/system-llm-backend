from typing import Dict, Any, List, Optional
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import Tool
from app.services.llm.base import BaseLLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """
    OpenRouter provider implementation using langchain-openai with OpenRouter endpoint.
    Uses endpoint: https://openrouter.ai/api/v1/chat/completions
    Supports open-source models like Llama 3.1, Qwen 2.5, Phi-3, and more.

    OpenRouter is OpenAI-compatible, so we reuse ChatOpenAI with custom base_url.
    """

    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenRouter provider.

        Args:
            model_name: OpenRouter model name (e.g., 'meta-llama/llama-3.1-8b-instruct')
            api_key: OpenRouter API key (if None, will use OPENROUTER_API_KEY env var)
            **kwargs: Additional configuration passed to ChatOpenAI
        """
        super().__init__(model_name, **kwargs)

        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

        # Initialize ChatOpenAI client pointing to OpenRouter
        self._client = self._create_client()

    def _create_client(self) -> ChatOpenAI:
        """
        Create ChatOpenAI client configured for OpenRouter.
        OpenRouter is OpenAI-compatible, so ChatOpenAI works seamlessly.
        """
        client_config = {
            "model": self.model_name,
            "base_url": self.base_url,
            "model_kwargs": {},
            "temperature": 1
        }

        # Add API key if provided
        if self.api_key:
            client_config["api_key"] = self.api_key

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
        Generate response from OpenRouter model (synchronous).

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        # Temporarily remove temperature to use model defaults
        original_temp = self._client.temperature
        original_max_tokens = self._client.max_tokens

        self._client.temperature = 1
        self._client.max_tokens = None

        try:
            response = self._client.invoke(langchain_messages)
            return response.content
        finally:
            # Restore original values
            self._client.temperature = original_temp
            self._client.max_tokens = original_max_tokens

    async def agenerate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from OpenRouter model (asynchronous).

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated text response
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        # Temporarily remove temperature
        original_temp = self._client.temperature
        original_max_tokens = self._client.max_tokens

        self._client.temperature = 1
        self._client.max_tokens = None

        try:
            response = await self._client.ainvoke(langchain_messages)
            return response.content
        finally:
            # Restore original values
            self._client.temperature = original_temp
            self._client.max_tokens = original_max_tokens

    async def agenerate_stream(self, messages: List[Dict[str, str]]):
        """
        Generate streaming response from OpenRouter model (asynchronous).
        Yields chunks of text as they are generated.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Yields:
            str: Text chunks as they are generated
        """
        # Convert messages to langchain format
        langchain_messages = self._convert_messages(messages)

        # Temporarily remove temperature
        original_temp = self._client.temperature
        original_max_tokens = self._client.max_tokens

        self._client.temperature = 1
        self._client.max_tokens = None

        try:
            # Stream response asynchronously
            async for chunk in self._client.astream(langchain_messages):
                if chunk.content:
                    yield chunk.content
        finally:
            # Restore original values
            self._client.temperature = original_temp
            self._client.max_tokens = original_max_tokens

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openrouter"

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information."""
        info = super().get_model_info()
        info.update({
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
        })
        return info

    async def agenerate_stream_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Tool],
        max_iterations: int = 10
    ):
        """
        Generate streaming response with tool calling support for OpenRouter.

        Note: Tool calling support varies by model on OpenRouter.
        Llama 3.1 has basic support, but may be less robust than GPT-4.

        Implements agentic loop with token-by-token streaming:
        model -> tool call -> tool result -> model -> stream response

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            tools: List of Langchain Tool objects
            max_iterations: Max iterations to prevent infinite loops

        Yields:
            Dict with 'type' (chunk/tool_call/tool_result) and 'content'
        """
        # Convert to langchain messages
        langchain_messages = self._convert_messages(messages)

        # Check if model supports tool calling
        if not self._supports_tool_calling():
            logger.warning(
                f"Model {self.model_name} may have limited tool calling support. "
                "Falling back to non-tool mode."
            )
            # Fall back to regular streaming without tool calling
            async for chunk in self.agenerate_stream(messages):
                yield {
                    "type": "chunk",
                    "content": chunk
                }
            return

        # Bind tools to the model
        model_with_tools = self._client.bind_tools(tools)

        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Tool calling iteration {iteration}/{max_iterations}")

            # Get response from model (non-streaming first to detect tool calls)
            response = await model_with_tools.ainvoke(langchain_messages)

            # Check if there are tool calls in the response
            if response.tool_calls:
                logger.info(f"LLM generated {len(response.tool_calls)} tool call(s)")

                # Add assistant message with tool calls to message history
                langchain_messages.append(response)

                # Process each tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_input = tool_call["args"]
                    tool_id = tool_call["id"]

                    logger.info(f"LLM called tool: {tool_name} with input: {tool_input}")

                    # Yield tool call event
                    yield {
                        "type": "tool_call",
                        "content": {
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_id": tool_id
                        }
                    }

                    # Find and execute the tool
                    tool_to_run = None
                    for tool in tools:
                        if tool.name == tool_name:
                            tool_to_run = tool
                            break

                    tool_message = None

                    if tool_to_run:
                        try:
                            # Execute the tool
                            tool_result = tool_to_run.func(**tool_input)
                            logger.info(f"Tool {tool_name} executed successfully")

                            # Yield tool result event
                            yield {
                                "type": "tool_result",
                                "content": {
                                    "tool_name": tool_name,
                                    "tool_id": tool_id,
                                    "result": tool_result
                                }
                            }

                            # Format tool result for LLM (JSON for structured data)
                            if isinstance(tool_result, dict):
                                tool_result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                            else:
                                tool_result_str = str(tool_result)

                            tool_message = ToolMessage(
                                content=tool_result_str,
                                tool_call_id=tool_id
                            )

                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}", exc_info=True)
                            yield {
                                "type": "tool_result",
                                "content": {
                                    "tool_name": tool_name,
                                    "tool_id": tool_id,
                                    "error": str(e)
                                }
                            }
                            # Create error message
                            tool_message = ToolMessage(
                                content=f"Error executing tool: {str(e)}",
                                tool_call_id=tool_id,
                                is_error=True
                            )

                    else:
                        logger.error(f"Tool not found: {tool_name}")
                        # Create error message for missing tool
                        tool_message = ToolMessage(
                            content=f"Error: Tool '{tool_name}' not found",
                            tool_call_id=tool_id,
                            is_error=True
                        )

                    # Add tool message to message history
                    if tool_message:
                        langchain_messages.append(tool_message)

            else:
                # No tool calls, stream LLM text response word-by-word
                if response.content:
                    logger.debug("LLM generated text response - streaming words")
                    # Stream response word-by-word for real-time typing effect
                    content = response.content
                    words = content.split()
                    for i, word in enumerate(words):
                        # Add space after word except for last word
                        token = word + (" " if i < len(words) - 1 else "")
                        yield {
                            "type": "chunk",
                            "content": token
                        }
                else:
                    logger.debug("Tool calling loop completed - no content to stream")

                logger.debug("Tool calling loop completed - LLM response ready")
                break

        if iteration >= max_iterations:
            logger.warning(f"Tool calling reached max iterations ({max_iterations})")
            yield {
                "type": "chunk",
                "content": "[Tool calling max iterations reached]"
            }

    def _supports_tool_calling(self) -> bool:
        """
        Check if the model supports tool calling.

        OpenRouter model support for tool calling:
        - Llama 3.1: Limited support
        - Qwen 2.5: Limited support
        - Phi-3: No tool support

        Returns:
            True if model likely supports tool calling, False otherwise
        """
        # Models known to support tool calling
        tool_supporting_models = [
            "meta-llama/llama-3.1",  # Llama 3.1 has basic support
            "qwen/qwen-2.5",  # Qwen 2.5 may have support
        ]

        for supported in tool_supporting_models:
            if supported in self.model_name:
                return True

        return False
