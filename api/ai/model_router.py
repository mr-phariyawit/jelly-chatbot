"""
Multi-model Router
Routes requests to appropriate Gemini model based on intent, complexity, and bot config.
Supports per-bot model override via bot.model_config.
"""

import json
import logging
from typing import Optional
from ai.llm_client import GeminiRESTClient
from ai.intent_classifier import IntentResult

logger = logging.getLogger(__name__)

# Available model tiers
MODEL_TIERS = {
    "fast": "gemini-2.0-flash",         # Simple queries, greetings, FAQ
    "quality": "gemini-2.5-flash",       # Complex analysis, complaints
}

DEFAULT_MODEL = "gemini-2.0-flash"


class ModelRouter:
    """Routes LLM requests to appropriate model based on context."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._clients: dict = {}  # model -> GeminiRESTClient (lazy init)

    def get_client(self, intent: Optional[IntentResult] = None, bot_model_config: Optional[str] = None) -> GeminiRESTClient:
        """
        Get the appropriate LLM client based on intent and bot config.

        Priority:
        1. Bot-specific model override (from bot.model_config)
        2. Intent-based model routing
        3. Default model
        """
        model = self._resolve_model(intent, bot_model_config)
        return self._get_or_create_client(model)

    def _resolve_model(self, intent: Optional[IntentResult], bot_model_config: Optional[str]) -> str:
        """Determine which model to use."""
        # 1. Check bot-specific override
        if bot_model_config:
            try:
                config = json.loads(bot_model_config)
                if config.get("model"):
                    logger.info(f"Using bot-configured model: {config['model']}")
                    return config["model"]
            except (json.JSONDecodeError, TypeError):
                pass

        # 2. Route by intent
        if intent:
            tier = intent.model_tier
            model = MODEL_TIERS.get(tier, DEFAULT_MODEL)
            logger.info(f"Model routed by intent '{intent.intent}' (tier={tier}): {model}")
            return model

        # 3. Default
        return DEFAULT_MODEL

    def _get_or_create_client(self, model: str) -> GeminiRESTClient:
        """Lazy-initialize and cache LLM clients per model."""
        if model not in self._clients:
            self._clients[model] = GeminiRESTClient(self.api_key, model)
            logger.info(f"Created LLM client for model: {model}")
        return self._clients[model]

    def get_model_info(self, intent: Optional[IntentResult] = None, bot_model_config: Optional[str] = None) -> dict:
        """Get routing info for logging/debugging."""
        model = self._resolve_model(intent, bot_model_config)
        return {
            "model": model,
            "tier": "fast" if model == MODEL_TIERS["fast"] else "quality",
            "reason": "bot_config" if bot_model_config else ("intent" if intent else "default"),
        }
