"""
Intent Classification Service
Classifies user messages into intents for smart routing.
Uses lightweight keyword matching first, falls back to LLM for ambiguous cases.
"""

import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Classification result."""
    intent: str          # greeting, faq, complaint, escalation, technical, chitchat
    confidence: float    # 0.0 - 1.0
    requires_rag: bool   # Whether to search knowledge base
    model_tier: str      # "fast" or "quality" - model routing hint


# Keyword patterns for fast classification (no LLM call needed)
INTENT_PATTERNS = {
    "greeting": {
        "patterns": [
            r"^(สวัสดี|หวัดดี|ดีครับ|ดีค่ะ|hi|hello|hey|good morning|good afternoon)\b",
            r"^(ดี$|สวัสดี$)",
        ],
        "requires_rag": False,
        "model_tier": "fast",
    },
    "escalation": {
        "patterns": [
            r"(ติดต่อเจ้าหน้าที่|คุยกับคน|ขอคุยกับ|ต้องการพูดกับ|โอเปอเรเตอร์)",
            r"(talk to (a )?human|speak to (an )?agent|operator|representative)",
        ],
        "requires_rag": False,
        "model_tier": "fast",
    },
    "complaint": {
        "patterns": [
            r"(ไม่พอใจ|ร้องเรียน|แย่มาก|ห่วยแตก|เงินหาย|ถูกหลอก|โกง)",
            r"(เรื่องเงิน|ค่าใช้จ่าย|refund|คืนเงิน|charge|billing)",
        ],
        "requires_rag": True,
        "model_tier": "quality",
    },
    "thanks": {
        "patterns": [
            r"^(ขอบคุณ|ขอบใจ|thanks?|thank you|thx)",
        ],
        "requires_rag": False,
        "model_tier": "fast",
    },
}


class IntentClassifier:
    """Classifies user messages into intents for routing."""

    def __init__(self, gemini_client=None):
        self.gemini = gemini_client

    def classify(self, message: str, history: list = None) -> IntentResult:
        """
        Classify user message intent.
        Uses fast keyword matching first, LLM classification for ambiguous cases.
        """
        message_lower = message.strip().lower()

        # 1. Fast keyword-based classification
        for intent, config in INTENT_PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(f"Intent classified by keyword: {intent}")
                    return IntentResult(
                        intent=intent,
                        confidence=0.9,
                        requires_rag=config["requires_rag"],
                        model_tier=config["model_tier"],
                    )

        # 2. Check message length/complexity for model routing
        is_complex = self._is_complex_query(message)

        # 3. Default: treat as FAQ/question that needs RAG
        return IntentResult(
            intent="faq",
            confidence=0.7,
            requires_rag=True,
            model_tier="quality" if is_complex else "fast",
        )

    def _is_complex_query(self, message: str) -> bool:
        """Heuristic check for query complexity."""
        # Long messages are likely complex
        if len(message) > 200:
            return True

        # Multiple questions
        question_marks = message.count("?") + message.count("？")
        if question_marks > 1:
            return True

        # Comparison/analysis keywords
        complex_keywords = [
            "เปรียบเทียบ", "วิเคราะห์", "อธิบาย", "ทำไม", "อย่างไร",
            "compare", "analyze", "explain", "why", "how does",
            "ข้อดี", "ข้อเสีย", "แตกต่าง", "ความแตกต่าง",
        ]
        if any(kw in message.lower() for kw in complex_keywords):
            return True

        return False

    def classify_with_llm(self, message: str, history: list = None) -> IntentResult:
        """
        LLM-based intent classification for ambiguous messages.
        Only called when keyword matching confidence is low.
        """
        if not self.gemini:
            return IntentResult(intent="faq", confidence=0.5, requires_rag=True, model_tier="fast")

        context = ""
        if history:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]])

        prompt = f"""Classify this user message into ONE category.
Categories: greeting, faq, complaint, escalation, technical, thanks, chitchat

{f"Recent context:{chr(10)}{context}{chr(10)}" if context else ""}
Message: {message}

Reply with ONLY the category name, nothing else."""

        try:
            result = self.gemini.generate_content(prompt, timeout=10).strip().lower()
            valid_intents = {"greeting", "faq", "complaint", "escalation", "technical", "thanks", "chitchat"}
            intent = result if result in valid_intents else "faq"

            requires_rag = intent in ("faq", "complaint", "technical")
            model_tier = "quality" if intent in ("complaint", "technical") else "fast"

            return IntentResult(
                intent=intent,
                confidence=0.8,
                requires_rag=requires_rag,
                model_tier=model_tier,
            )
        except Exception as e:
            logger.warning(f"LLM intent classification failed: {e}")
            return IntentResult(intent="faq", confidence=0.5, requires_rag=True, model_tier="fast")
