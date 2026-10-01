"""
Optional External LLM API Client for the NOVA Chatbot.

Provides configurable integration with any OpenAI-compatible API endpoint
(OpenAI, OpenRouter, Groq, Ollama) using Python standard library urllib.
Safely falls back on missing keys, timeouts, or network failures.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_SYSTEM_PROMPT = (
    "You are NOVA, an intelligent, helpful, and concise AI chatbot for Task 06 "
    "of the Auspify Python Internship. Provide clear, accurate answers, format code "
    "cleanly, and maintain an encouraging, professional tone."
)


class LLMClient:
    """Zero-dependency HTTP client for OpenAI-compatible Chat Completion APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 10,
    ):
        """Initialize client from environment variables or explicit parameters."""
        self.api_key = (
            api_key
            or os.environ.get("CHATBOT_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        ).strip()
        self.base_url = (
            base_url
            or os.environ.get("CHATBOT_API_BASE")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self.model = (
            model
            or os.environ.get("CHATBOT_MODEL")
            or "gpt-4o-mini"
        ).strip()
        self.timeout = timeout or int(os.environ.get("CHATBOT_TIMEOUT_SECONDS", "10"))

    def is_configured(self) -> bool:
        """Return True if a non-empty, non-placeholder API key is available."""
        if not self.api_key:
            return False
        # Disallow sample placeholder keys
        if "your_" in self.api_key.lower() or "example" in self.api_key.lower():
            return False
        return len(self.api_key) > 8

    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Call external chat completion endpoint.

        Args:
            messages: List of message dicts: [{'role': 'user', 'content': '...'}]
            system_prompt: Guiding system behavior instructions.

        Returns:
            Tuple of (response_text, error_message). One will be None.
        """
        if not self.is_configured():
            return None, "External LLM API key not configured. Using local NLP engine."

        url = f"{self.base_url}/chat/completions"
        payload_messages = [{"role": "system", "content": system_prompt}] + messages
        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": 0.7,
            "max_tokens": 500,
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "Auspify-Chatbot/1.0",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    raw_body = response.read().decode("utf-8")
                    result_json = json.loads(raw_body)
                    choices = result_json.get("choices", [])
                    if choices:
                        message_obj = choices[0].get("message", {})
                        content = message_obj.get("content", "").strip()
                        return content, None
                    return None, "Empty choices returned from API."
                return None, f"API returned HTTP status {response.status}."
        except urllib.error.HTTPError as err:
            return None, f"HTTP Error {err.code}: {err.reason}"
        except urllib.error.URLError as err:
            return None, f"Network connection error: {err.reason}"
        except TimeoutError:
            return None, f"External API timed out after {self.timeout}s."
        except Exception as err:
            return None, f"Unexpected error during API request: {err}"
