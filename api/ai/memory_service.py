"""
Conversation Memory Service
Manages conversation history with automatic summarization for long conversations.
Reduces token usage by compressing older messages into concise summaries.
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

logger = logging.getLogger(__name__)

# When conversation exceeds this many messages, summarize older ones
SUMMARIZE_THRESHOLD = 10
# Keep this many recent messages in full detail
RECENT_MESSAGES_KEEP = 5
# Max summary length (characters)
MAX_SUMMARY_LENGTH = 500


class MemoryService:
    """Manages conversation history with summarization for long conversations."""

    def __init__(self, gemini_client=None):
        self.gemini = gemini_client

    def get_conversation_context(
        self, db: Session, session_id: str, max_recent: int = RECENT_MESSAGES_KEEP
    ) -> Dict[str, any]:
        """
        Get conversation context with automatic summarization.

        Returns:
            {
                "summary": "optional summary of older messages",
                "recent_messages": [{"role": ..., "content": ...}],
                "total_messages": int,
            }
        """
        from models import Message
        from app.cache import cache_get, cache_set

        # Check cache first
        cache_key = f"conv:{session_id}"
        cached = cache_get("memory", cache_key)

        # Get total message count
        total = db.query(Message).filter(Message.session_id == session_id).count()

        # Get recent messages (always fresh from DB)
        recent = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(desc(Message.timestamp))
            .limit(max_recent)
            .all()
        )
        recent.reverse()  # Chronological order
        recent_messages = [{"role": m.role, "content": m.content} for m in recent if m.content]

        # If conversation is short, no summary needed
        if total <= SUMMARIZE_THRESHOLD:
            return {
                "summary": None,
                "recent_messages": recent_messages,
                "total_messages": total,
            }

        # Check if we have a cached summary and it's still valid
        if cached and cached.get("summarized_up_to", 0) >= (total - max_recent):
            return {
                "summary": cached["summary"],
                "recent_messages": recent_messages,
                "total_messages": total,
            }

        # Need to generate summary for older messages
        summary = self._summarize_older_messages(db, session_id, total, max_recent)

        # Cache the summary
        if summary:
            cache_set("memory", cache_key, {
                "summary": summary,
                "summarized_up_to": total - max_recent,
            }, ttl_seconds=1800)  # 30 min TTL

        return {
            "summary": summary,
            "recent_messages": recent_messages,
            "total_messages": total,
        }

    def _summarize_older_messages(
        self, db: Session, session_id: str, total: int, keep_recent: int
    ) -> Optional[str]:
        """Summarize older messages using LLM."""
        if not self.gemini:
            return None

        from models import Message

        # Get older messages (everything except recent)
        older_count = total - keep_recent
        older = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.timestamp.asc())
            .limit(older_count)
            .all()
        )

        if not older:
            return None

        # Build conversation text for summarization
        conv_text = "\n".join([
            f"{'User' if m.role == 'user' else 'AI'}: {m.content}"
            for m in older if m.content
        ])

        # Truncate if too long
        if len(conv_text) > 3000:
            conv_text = conv_text[:3000] + "..."

        prompt = f"""Summarize this conversation history concisely (max 3 sentences, in Thai).
Focus on: main topics discussed, any unresolved issues, and user preferences.

Conversation:
{conv_text}

Summary:"""

        try:
            summary = self.gemini.generate_content(prompt, timeout=15)
            return summary.strip()[:MAX_SUMMARY_LENGTH]
        except Exception as e:
            logger.warning(f"Conversation summarization failed: {e}")
            return None

    def format_context_for_prompt(self, context: Dict) -> str:
        """Format conversation context for inclusion in LLM prompt."""
        parts = []

        if context.get("summary"):
            parts.append(f"สรุปบทสนทนาก่อนหน้า: {context['summary']}")

        if context.get("recent_messages"):
            recent_str = "\n".join([
                f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in context["recent_messages"]
            ])
            parts.append(f"บทสนทนาล่าสุด:\n{recent_str}")

        return "\n\n".join(parts)
