"""Claude API client wrapper for paper analysis."""

import os
from typing import Optional, Dict, Any
import time
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

from .prompts import PromptTemplate, PromptType


class ClaudeClient:
    """
    Wrapper for Claude API client with error handling and retry logic.

    Handles:
    - API authentication
    - Context window management (up to 200k tokens)
    - Structured prompts for paper analysis
    - Error handling and retries
    - Token usage tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Claude API key. If None, will look for ANTHROPIC_API_KEY env var.
            model: Claude model to use (default: claude-sonnet-4-20250514)
            max_tokens: Maximum tokens in response (default: 4096)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            max_retries: Maximum number of retries on failure (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 1.0)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided or set in ANTHROPIC_API_KEY environment variable"
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Track usage statistics
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0

    def analyze_paper(
        self,
        paper_text: str,
        metadata: Dict[str, Any],
        prompt_type: PromptType = PromptType.COMPREHENSIVE,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a paper using Claude AI.

        Args:
            paper_text: Full text content of the paper
            metadata: Paper metadata (title, authors, year, etc.)
            prompt_type: Type of analysis to perform
            custom_instructions: Optional custom instructions to add to the prompt

        Returns:
            Dict containing:
                - analysis: The generated analysis text
                - model: Model used
                - input_tokens: Number of input tokens
                - output_tokens: Number of output tokens
                - finish_reason: Reason for completion

        Raises:
            APIError: If API request fails after all retries
            ValueError: If paper_text is empty or too long
        """
        if not paper_text or not paper_text.strip():
            raise ValueError("Paper text cannot be empty")

        # Build the prompt
        prompt_template = PromptTemplate(prompt_type)
        prompt = prompt_template.build(
            paper_text=paper_text,
            metadata=metadata,
            custom_instructions=custom_instructions,
        )

        # Make API call with retry logic
        response = self._call_with_retry(prompt)

        # Update usage statistics
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        self.total_requests += 1

        # Extract the text content from the response
        analysis_text = ""
        if response.content:
            for block in response.content:
                if hasattr(block, "text"):
                    analysis_text += block.text

        return {
            "analysis": analysis_text,
            "model": response.model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "finish_reason": response.stop_reason,
        }

    def _call_with_retry(self, prompt: str) -> Any:
        """
        Call Claude API with exponential backoff retry logic.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            API response

        Raises:
            APIError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )
                return response

            except RateLimitError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                    continue
                raise

            except APIConnectionError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise

            except APIError as e:
                # Don't retry on client errors (4xx), only server errors (5xx)
                if hasattr(e, 'status_code') and 400 <= e.status_code < 500:
                    raise

                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                raise

        # If we get here, all retries failed
        raise last_error

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        This is a rough estimation (4 characters ≈ 1 token).
        For precise counting, use the tokenizer.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get usage statistics for this client instance.

        Returns:
            Dict with total_requests, total_input_tokens, total_output_tokens
        """
        return {
            "total_requests": self.total_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }

    def reset_usage_stats(self):
        """Reset usage statistics to zero."""
        self.total_requests = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
