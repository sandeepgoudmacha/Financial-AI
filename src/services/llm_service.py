"""
Valura AI — LLM Service (Groq).

Production-grade LLM client with:
- Groq API integration (OpenAI-compatible)
- Structured output support via Pydantic
- Retry logic with exponential backoff
- Timeout handling
- Token usage tracking
- Streaming support
- Model fallback chain
"""

from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Optional, Type, TypeVar

from groq import AsyncGroq, APIError, APITimeoutError, RateLimitError
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.core.config import get_settings
from src.core.exceptions import LLMError, LLMTimeoutError
from src.core.logging import get_logger

logger = get_logger("llm_service")

T = TypeVar("T", bound=BaseModel)


class TokenUsage(BaseModel):
    """Track token usage across requests."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMService:
    """
    Async Groq LLM client with production features.

    Provides:
    - generate(): Single completion
    - generate_structured(): Pydantic-parsed completion
    - stream(): Streaming token generation
    - Model fallback on failure
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncGroq(api_key=settings.groq_api_key.get_secret_value())
        self._primary_model = settings.groq_model
        self._fast_model = settings.groq_fast_model
        self._temperature = settings.groq_temperature
        self._max_tokens = settings.groq_max_tokens
        self._timeout = settings.request_timeout
        self._total_usage = TokenUsage()

    @property
    def usage(self) -> TokenUsage:
        return self._total_usage

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        Generate a single completion.

        Args:
            messages: Chat messages in OpenAI format.
            model: Override model selection.
            temperature: Override temperature.
            max_tokens: Override max tokens.
            json_mode: Force JSON output.

        Returns:
            Generated text content.

        Raises:
            LLMError: If all retries fail.
            LLMTimeoutError: If request times out.
        """
        model = model or self._primary_model
        try:
            return await self._call_with_fallback(
                messages=messages,
                model=model,
                temperature=temperature or self._temperature,
                max_tokens=max_tokens or self._max_tokens,
                json_mode=json_mode,
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        response_model: Type[T],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """
        Generate a completion and parse it into a Pydantic model.

        Instructs the LLM to output JSON matching the schema,
        then validates and parses the response.

        Args:
            messages: Chat messages.
            response_model: Pydantic model class to parse into.
            model: Override model.
            temperature: Override temperature.

        Returns:
            Parsed Pydantic model instance.
        """
        schema = response_model.model_json_schema()
        schema_instruction = (
            f"\n\nYou MUST respond with valid JSON matching this exact schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```\n"
            f"Respond ONLY with the JSON object, no other text."
        )

        # Append schema instruction to last user or system message
        augmented_messages = messages.copy()
        if augmented_messages:
            last_msg = augmented_messages[-1].copy()
            last_msg["content"] = last_msg["content"] + schema_instruction
            augmented_messages[-1] = last_msg

        raw = await self.generate(
            messages=augmented_messages,
            model=model,
            temperature=temperature or 0.1,  # Low temp for structured output
            json_mode=True,
        )

        # Parse JSON from response (handle markdown code blocks)
        json_str = raw.strip()
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            json_str = "\n".join(lines[1:-1]) if len(lines) > 2 else json_str

        try:
            data = json.loads(json_str)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse structured output: {e}. Raw: {raw[:200]}")
            # Attempt to extract JSON from mixed content
            import re
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return response_model.model_validate(data)
            raise LLMError(f"Failed to parse structured output: {e}", model=model or self._primary_model)

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens from the LLM.

        Yields individual tokens/chunks as they arrive.

        Args:
            messages: Chat messages.
            model: Override model.
            temperature: Override temperature.
            max_tokens: Override max tokens.

        Yields:
            String tokens as they are generated.
        """
        model = model or self._primary_model
        try:
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature or self._temperature,
                max_tokens=max_tokens or self._max_tokens,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APITimeoutError:
            raise LLMTimeoutError(model=model)
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise LLMError(f"Streaming failed: {e}", model=model)

    async def _call_with_fallback(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> str:
        """Try primary model, fall back to fast model on failure."""
        models_to_try = [model]
        if model != self._fast_model:
            models_to_try.append(self._fast_model)

        last_error: Optional[Exception] = None
        for m in models_to_try:
            try:
                return await self._make_request(
                    messages=messages,
                    model=m,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
            except RateLimitError as e:
                logger.warning(f"Rate limited on {m}, trying fallback...")
                last_error = e
                continue
            except APITimeoutError as e:
                logger.warning(f"Timeout on {m}, trying fallback...")
                last_error = e
                continue
            except APIError as e:
                logger.warning(f"API error on {m}: {e}, trying fallback...")
                last_error = e
                continue

        raise LLMError(
            f"All models failed. Last error: {last_error}",
            model=model,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APIError, RateLimitError)),
        reraise=True,
    )
    async def _make_request(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool = False,
    ) -> str:
        """Make a single LLM request with retry logic."""
        start = time.perf_counter()

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.chat.completions.create(**kwargs)
        except APITimeoutError:
            raise LLMTimeoutError(model=model)

        duration_ms = (time.perf_counter() - start) * 1000
        content = response.choices[0].message.content or ""

        # Track usage
        if response.usage:
            self._total_usage.prompt_tokens += response.usage.prompt_tokens
            self._total_usage.completion_tokens += response.usage.completion_tokens
            self._total_usage.total_tokens += response.usage.total_tokens

        logger.info(
            f"LLM [{model}] completed in {duration_ms:.0f}ms | "
            f"tokens: {response.usage.total_tokens if response.usage else 'N/A'}"
        )
        return content

    async def close(self) -> None:
        """Cleanup client resources."""
        await self._client.close()
