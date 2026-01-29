"""
Response Quality Guard
Validates AI responses before sending to users.
Checks for hallucination, appropriate tone, and content safety.
"""

import re
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Max response length (characters) - LINE message limit is 5000
MAX_RESPONSE_LENGTH = 4500
# Min response length to avoid empty/too-short responses
MIN_RESPONSE_LENGTH = 5


@dataclass
class QualityResult:
    """Quality check result."""
    passed: bool
    original_response: str
    cleaned_response: str
    issues: list  # List of detected issues
    confidence_score: float  # 0.0 - 1.0


class QualityGuard:
    """Validates and cleans AI responses before delivery."""

    def __init__(self, gemini_client=None):
        self.gemini = gemini_client

    def check(self, response: str, rag_context: str = "", query: str = "") -> QualityResult:
        """
        Run quality checks on AI response.

        Checks:
        1. Length validation
        2. Content safety (no sensitive data leaks)
        3. Markdown cleanup (for LINE)
        4. Hallucination detection (if RAG context available)
        5. Language consistency
        """
        issues = []
        cleaned = response
        confidence = 1.0

        # 1. Length check
        if len(cleaned) < MIN_RESPONSE_LENGTH:
            issues.append("response_too_short")
            confidence -= 0.3

        if len(cleaned) > MAX_RESPONSE_LENGTH:
            cleaned = cleaned[:MAX_RESPONSE_LENGTH] + "..."
            issues.append("response_truncated")

        # 2. Content safety - check for leaked system prompts or API keys
        safety_issues = self._check_content_safety(cleaned)
        if safety_issues:
            issues.extend(safety_issues)
            confidence -= 0.5

        # 3. Markdown cleanup for LINE
        cleaned = self._clean_markdown(cleaned)

        # 4. Hallucination check
        if self._detect_hallucination_heuristic(cleaned, rag_context, query):
            issues.append("potential_hallucination")
            confidence -= 0.2

        # 5. Repetition check
        if self._detect_repetition(cleaned):
            cleaned = self._remove_repetition(cleaned)
            issues.append("repetition_removed")

        return QualityResult(
            passed=len(issues) == 0 or all(i in ("response_truncated", "repetition_removed") for i in issues),
            original_response=response,
            cleaned_response=cleaned,
            issues=issues,
            confidence_score=max(0.0, confidence),
        )

    def _check_content_safety(self, text: str) -> list:
        """Check for sensitive data leaks in the response."""
        issues = []

        # API key patterns
        if re.search(r"AIza[0-9A-Za-z_-]{35}", text):
            issues.append("leaked_api_key")

        # System prompt leak
        system_prompt_markers = ["system_prompt", "SYSTEM_PROMPT", "คุณคือ AI", "กฎสำคัญในการตอบ"]
        if any(marker in text for marker in system_prompt_markers):
            issues.append("system_prompt_leak")

        # Internal error messages
        if re.search(r"(Traceback|Exception|Error:.*line \d+)", text):
            issues.append("internal_error_leak")

        return issues

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting for LINE compatibility."""
        # Bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # Italic
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # Headers
        text = re.sub(r'#{1,6}\s', '', text)
        # Bullet points → Thai bullet
        text = re.sub(r'^[-*]\s', '• ', text, flags=re.MULTILINE)
        # Code blocks
        text = re.sub(r'```[a-z]*\n?', '', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        return text

    def _detect_hallucination_heuristic(self, response: str, rag_context: str, query: str) -> bool:
        """
        Simple heuristic hallucination detection.
        Checks if the response makes specific claims not grounded in the RAG context.
        """
        # If no RAG context was provided and response claims to use it, flag it
        if not rag_context and "ตามข้อมูลที่มี" in response:
            return True

        # Check for specific number/date claims that aren't in the context
        numbers_in_response = set(re.findall(r'\b\d{3,}\b', response))
        numbers_in_context = set(re.findall(r'\b\d{3,}\b', rag_context))
        novel_numbers = numbers_in_response - numbers_in_context

        # If response introduces many new specific numbers not in context, suspicious
        if len(novel_numbers) > 3:
            return True

        return False

    def _detect_repetition(self, text: str) -> bool:
        """Detect if the response has significant repetition."""
        sentences = [s.strip() for s in re.split(r'[.!?\n]', text) if len(s.strip()) > 20]
        if len(sentences) < 2:
            return False

        seen = set()
        duplicates = 0
        for s in sentences:
            normalized = s.lower().strip()
            if normalized in seen:
                duplicates += 1
            seen.add(normalized)

        return duplicates >= 2

    def _remove_repetition(self, text: str) -> str:
        """Remove repeated sentences/paragraphs."""
        lines = text.split('\n')
        seen = set()
        result = []
        for line in lines:
            normalized = line.strip().lower()
            if normalized and normalized in seen:
                continue
            if normalized:
                seen.add(normalized)
            result.append(line)
        return '\n'.join(result)
