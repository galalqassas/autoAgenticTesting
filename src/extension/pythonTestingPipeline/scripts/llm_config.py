#!/usr/bin/env python3
"""
LLM Configuration and Fallback Logic

This module handles API key rotation and model fallback for the Python Testing Pipeline.
Add new API keys to the .env file as GROQ_API_KEY_1, GROQ_API_KEY_2, etc.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Try to import openai
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def load_dotenv():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


# Load .env on module import
load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for LLM API access."""

    # API endpoint
    BASE_URL = "https://api.groq.com/openai/v1"

    # Models in order of preference (will try each on failure)
    MODELS = [
        "openai/gpt-oss-120b",
        "groq/compound",
        "groq/compound-mini",
        "moonshotai/kimi-k2-instruct-0905",
        "moonshotai/kimi-k2-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "openai/gpt-oss-20b",
    ]

    # API keys loaded from environment (in order of preference)
    @staticmethod
    def get_api_keys() -> list[str]:
        """
        Get all available API keys from environment.
        Looks for GROQ_API_KEY, GROQ_API_KEY_1, GROQ_API_KEY_2, etc.
        """
        keys = []

        # Check for the main key first
        main_key = os.environ.get("GROQ_API_KEY")
        if main_key:
            keys.append(main_key)

        # Check for numbered keys (GROQ_API_KEY_1, GROQ_API_KEY_2, ...)
        i = 1
        while True:
            key = os.environ.get(f"GROQ_API_KEY_{i}")
            if key:
                keys.append(key)
                i += 1
            else:
                break

        return keys


class LLMClient:
    """
    LLM Client with automatic API key rotation and model fallback.

    When a rate limit (429) or other error is encountered:
    1. Try the next model in the list
    2. If all models fail, try the next API key
    3. If all API keys fail, raise an error or return mock response
    """

    def __init__(self, use_mock_on_failure: bool = True):
        self.api_keys = LLMConfig.get_api_keys()
        self.models = LLMConfig.MODELS.copy()
        self.current_key_index = 0
        self.current_model_index = 0
        self.use_mock_on_failure = use_mock_on_failure
        self._client: Optional[openai.OpenAI] = None

        if not self.api_keys:
            print("⚠️  No API keys found. Add GROQ_API_KEY to .env file.")

        self._init_client()

    def _init_client(self):
        """Initialize or reinitialize the OpenAI client with current API key."""
        if not OPENAI_AVAILABLE:
            return

        if self.api_keys and self.current_key_index < len(self.api_keys):
            # Disable auto-retries to handle them ourselves
            self._client = openai.OpenAI(
                api_key=self.api_keys[self.current_key_index],
                base_url=LLMConfig.BASE_URL,
                max_retries=0,  # We handle retries ourselves
                timeout=30.0,
            )

    @property
    def current_model(self) -> str:
        """Get the current model being used."""
        return self.models[self.current_model_index]

    @property
    def current_api_key(self) -> Optional[str]:
        """Get the current API key (masked for display)."""
        if self.api_keys and self.current_key_index < len(self.api_keys):
            key = self.api_keys[self.current_key_index]
            return f"{key[:8]}...{key[-4:]}"
        return None

    def _try_next_model(self) -> bool:
        """Try switching to the next model. Returns True if successful."""
        if self.current_model_index < len(self.models) - 1:
            self.current_model_index += 1
            print(f"   ⚡ Switching to model: {self.current_model}")
            return True
        return False

    def _try_next_api_key(self) -> bool:
        """Try switching to the next API key. Returns True if successful."""
        if self.current_key_index < len(self.api_keys) - 1:
            self.current_key_index += 1
            self.current_model_index = 0  # Reset to first model
            self._init_client()
            print(f"   🔑 Switching to API key: {self.current_api_key}")
            return True
        return False

    def _reset_for_new_request(self):
        """Reset model index for a new request (keeps current API key if working)."""
        # Don't reset - keep current working configuration
        pass

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> tuple[str, bool]:
        """
        Call the LLM with automatic fallback.

        Returns:
            tuple: (response_text, is_mock)
        """
        if not OPENAI_AVAILABLE:
            return self._mock_response(system_prompt, user_prompt), True

        if not self._client:
            return self._mock_response(system_prompt, user_prompt), True

        last_error = None
        attempts = 0
        max_attempts = len(self.models) * len(self.api_keys) * max_retries

        while attempts < max_attempts:
            attempts += 1

            try:
                response = self._client.chat.completions.create(
                    model=self.current_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                )
                return response.choices[0].message.content, False

            except Exception as e:
                last_error = e
                error_str = str(e)
                error_type = type(e).__name__

                # Check for rate limit error (429) or quota exceeded
                is_rate_limit = (
                    "429" in error_str
                    or "rate_limit" in error_str.lower()
                    or "too many requests" in error_str.lower()
                    or "RateLimitError" in error_type
                )
                is_model_error = "model" in error_str.lower() and (
                    "not found" in error_str.lower() or "invalid" in error_str.lower()
                )

                if is_rate_limit or is_model_error:
                    print(
                        f"   ⚠️  {'Rate limit' if is_rate_limit else 'Model error'}: {self.current_model}"
                    )

                    # Try next model first
                    if self._try_next_model():
                        continue

                    # If all models exhausted, try next API key
                    if self._try_next_api_key():
                        continue

                    # All options exhausted
                    break
                else:
                    # For other errors, retry with backoff
                    print(f"   ⚠️  LLM Error ({error_type}): {error_str[:100]}")
                    time.sleep(1)

        # All retries exhausted
        if self.use_mock_on_failure:
            print("   ⚠️  All API options exhausted. Using mock response.")
            return self._mock_response(system_prompt, user_prompt), True
        else:
            raise RuntimeError(f"LLM call failed after all retries: {last_error}")

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a mock response when API is unavailable."""
        if (
            "identify" in system_prompt.lower()
            or "test_scenarios" in system_prompt.lower()
        ):
            return """{
  "test_scenarios": [
    {"scenario_description": "Test main function with valid input", "priority": "High"},
    {"scenario_description": "Test main function with empty input", "priority": "Medium"},
    {"scenario_description": "Test main function with invalid type", "priority": "Medium"},
    {"scenario_description": "Test edge case with very large input", "priority": "Low"}
  ]
}"""
        elif "pytest" in system_prompt.lower() or "generate" in system_prompt.lower():
            return '''import pytest

def test_main_function_with_valid_input():
    """Test that the main function works with valid input."""
    assert True

def test_main_function_with_empty_input():
    """Test that the main function handles empty input."""
    assert True

def test_main_function_with_invalid_type():
    """Test that the main function raises appropriate error for invalid types."""
    with pytest.raises((TypeError, ValueError)):
        pass

def test_edge_case_with_very_large_input():
    """Test behavior with very large input values."""
    assert True
'''
        elif "evaluat" in system_prompt.lower():
            return """{
  "execution_summary": {"total_tests": 4, "passed": 4, "failed": 0},
  "code_coverage_percentage": 85.0,
  "actionable_recommendations": ["Add more edge case tests", "Improve error handling coverage"],
  "security_issues": [],
  "has_severe_security_issues": false
}"""
        else:
            return '{"status": "mock_response", "message": "API unavailable"}'


# Convenience function for simple usage
def create_llm_client(use_mock_on_failure: bool = True) -> LLMClient:
    """Create and return a configured LLM client."""
    return LLMClient(use_mock_on_failure=use_mock_on_failure)
