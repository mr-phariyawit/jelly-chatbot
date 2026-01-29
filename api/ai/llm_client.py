"""
Gemini LLM Client
REST-based client for Google Gemini API (avoids gRPC credential issues on Cloud Run).
"""

import json
import logging
import requests
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class GeminiRESTClient:
    """Gemini API client using REST instead of gRPC to avoid credential issues."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.last_token_usage: Optional[dict] = None

    def generate_content(self, prompt: str, timeout: int = 60) -> str:
        """Generate content using REST API."""
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(url, json=payload, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            # Extract token usage if available
            usage = data.get("usageMetadata", {})
            self.last_token_usage = {
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
                "total_tokens": usage.get("totalTokenCount", 0)
            }

            return text
        else:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text[:200]}")

    def generate_content_stream(self, prompt: str, timeout: int = 60):
        """Generate content with streaming using REST API (SSE)."""
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        response = requests.post(url, json=payload, timeout=timeout, stream=True)

        if response.status_code != 200:
            raise Exception(f"Gemini Streaming API error: {response.status_code} - {response.text[:200]}")

        import json
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    try:
                        data = json.loads(decoded[6:])
                        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if text:
                            yield text

                        # Capture token usage from the final chunk
                        usage = data.get("usageMetadata")
                        if usage:
                            self.last_token_usage = {
                                "prompt_tokens": usage.get("promptTokenCount", 0),
                                "completion_tokens": usage.get("candidatesTokenCount", 0),
                                "total_tokens": usage.get("totalTokenCount", 0)
                            }
                    except json.JSONDecodeError:
                        continue

    def generate_with_tools(
        self, prompt: str, tools: List[Dict], timeout: int = 60
    ) -> Dict:
        """
        Generate content with function calling support.
        Returns dict with either 'text' or 'function_call' depending on model decision.

        Returns:
            {"type": "text", "content": "..."} or
            {"type": "function_call", "name": "...", "args": {...}}
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": tools,
        }

        response = requests.post(url, json=payload, timeout=timeout)

        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text[:200]}")

        data = response.json()
        usage = data.get("usageMetadata", {})
        self.last_token_usage = {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        }

        # Check if the model wants to call a function
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for part in parts:
            if "functionCall" in part:
                fc = part["functionCall"]
                return {
                    "type": "function_call",
                    "name": fc.get("name", ""),
                    "args": fc.get("args", {}),
                }

        # Otherwise return text
        text = parts[0].get("text", "") if parts else ""
        return {"type": "text", "content": text}

    def generate_with_tool_result(
        self, prompt: str, tool_name: str, tool_args: Dict, tool_result: Dict,
        tools: List[Dict], timeout: int = 60
    ) -> str:
        """
        Continue generation after a function call by providing the tool result.
        Sends the full conversation: user prompt → function call → function response → final answer.
        """
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]},
                {"role": "model", "parts": [{"functionCall": {"name": tool_name, "args": tool_args}}]},
                {"role": "function", "parts": [{"functionResponse": {"name": tool_name, "response": tool_result}}]},
            ],
            "tools": tools,
        }

        response = requests.post(url, json=payload, timeout=timeout)

        if response.status_code != 200:
            raise Exception(f"Gemini API error: {response.status_code} - {response.text[:200]}")

        data = response.json()
        usage = data.get("usageMetadata", {})
        self.last_token_usage = {
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "total_tokens": usage.get("totalTokenCount", 0),
        }

        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return text

    def embed_content(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> list:
        """Generate embeddings using REST API (gemini-embedding-001)."""
        url = f"{self.base_url}/models/gemini-embedding-001:embedContent?key={self.api_key}"
        payload = {
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": 768  # Match existing Vector(768) in database
        }

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            return data.get("embedding", {}).get("values", [])
        else:
            raise Exception(f"Embedding API error: {response.status_code} - {response.text[:200]}")
