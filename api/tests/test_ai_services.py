"""
Unit tests for AI services (LLM client, RAG service, Vision service, Processor).
Uses mocks to avoid real API calls.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock heavy Google Cloud dependencies that aren't installed locally
for mod_name in [
    "google.generativeai", "google.cloud.storage", "google.cloud.iam",
    "google.cloud.iam_credentials_v1", "google.cloud.secretmanager",
    "google.auth", "google.auth.transport", "google.auth.transport.requests",
    "google.auth.compute_engine", "google.auth.compute_engine.credentials",
    "pgvector", "pgvector.sqlalchemy", "linebot", "linebot.v3",
    "linebot.v3.exceptions", "linebot.v3.messaging", "jira",
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Mock pgvector.sqlalchemy.Vector to return a dummy column type
mock_pgvector = sys.modules["pgvector.sqlalchemy"]
mock_pgvector.Vector = lambda dim: None


class TestGeminiRESTClient(unittest.TestCase):
    """Tests for ai/llm_client.py"""

    def setUp(self):
        from ai.llm_client import GeminiRESTClient
        self.client = GeminiRESTClient(api_key="test-key", model="gemini-2.0-flash")

    @patch("ai.llm_client.requests.post")
    def test_generate_content_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "Hello!"}]}}],
                "usageMetadata": {
                    "promptTokenCount": 10,
                    "candidatesTokenCount": 5,
                    "totalTokenCount": 15,
                },
            },
        )

        result = self.client.generate_content("Say hello")
        self.assertEqual(result, "Hello!")
        self.assertEqual(self.client.last_token_usage["total_tokens"], 15)

    @patch("ai.llm_client.requests.post")
    def test_generate_content_api_error(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=500,
            text="Internal server error",
        )

        with self.assertRaises(Exception) as ctx:
            self.client.generate_content("Say hello")
        self.assertIn("Gemini API error: 500", str(ctx.exception))

    @patch("ai.llm_client.requests.post")
    def test_embed_content_success(self, mock_post):
        fake_embedding = [0.1] * 768
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"embedding": {"values": fake_embedding}},
        )

        result = self.client.embed_content("test query")
        self.assertEqual(len(result), 768)
        self.assertEqual(result[0], 0.1)

    @patch("ai.llm_client.requests.post")
    def test_generate_content_stream(self, mock_post):
        # Simulate SSE lines
        lines = [
            b'data: {"candidates": [{"content": {"parts": [{"text": "Hello"}]}}]}',
            b'data: {"candidates": [{"content": {"parts": [{"text": " World"}]}}]}',
            b'data: {"candidates": [{"content": {"parts": [{"text": "!"}]}}], "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 3, "totalTokenCount": 8}}',
        ]
        mock_response = MagicMock(status_code=200)
        mock_response.iter_lines.return_value = lines
        mock_post.return_value = mock_response

        tokens = list(self.client.generate_content_stream("Say hello"))
        self.assertEqual(tokens, ["Hello", " World", "!"])
        self.assertEqual(self.client.last_token_usage["total_tokens"], 8)


class TestIngestionServiceChunking(unittest.TestCase):
    """Tests for semantic chunking with overlap in ingestion_service.py"""

    def setUp(self):
        from ingestion_service import IngestionService
        self.service = IngestionService()

    def test_small_text_single_chunk(self):
        text = "Hello world. This is a test."
        chunks = self.service.chunk_text(text, chunk_size=1000, overlap=200)
        self.assertEqual(len(chunks), 1)

    def test_paragraph_splitting(self):
        para1 = "A" * 500
        para2 = "B" * 500
        para3 = "C" * 500
        text = f"{para1}\n\n{para2}\n\n{para3}"

        chunks = self.service.chunk_text(text, chunk_size=600, overlap=0)
        self.assertTrue(len(chunks) >= 2)

    def test_overlap_applied(self):
        para1 = "First paragraph content here."
        para2 = "Second paragraph content here."
        para3 = "Third paragraph content here."
        text = f"{'x' * 500}\n\n{'y' * 500}\n\n{'z' * 500}"

        chunks_no_overlap = self.service.chunk_text(text, chunk_size=600, overlap=0)
        chunks_with_overlap = self.service.chunk_text(text, chunk_size=600, overlap=200)

        # Overlapped chunks should be longer (contain prefix from previous)
        if len(chunks_with_overlap) > 1:
            self.assertTrue(len(chunks_with_overlap[1]) > len(chunks_no_overlap[1]))

    def test_sentence_splitting_for_large_paragraph(self):
        # One big paragraph with sentences
        text = "This is sentence one. This is sentence two. This is sentence three. " * 20
        chunks = self.service.chunk_text(text, chunk_size=200, overlap=0)
        self.assertTrue(len(chunks) >= 3)
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 250)  # Allow some flexibility

    def test_empty_text(self):
        chunks = self.service.chunk_text("", chunk_size=1000, overlap=200)
        self.assertEqual(len(chunks), 0)

    def test_no_empty_chunks(self):
        text = "\n\n\n\nHello\n\n\n\nWorld\n\n\n\n"
        chunks = self.service.chunk_text(text, chunk_size=1000, overlap=0)
        for chunk in chunks:
            self.assertTrue(len(chunk.strip()) > 0)


class TestIngestionServiceBatchEmbedding(unittest.TestCase):
    """Tests for batch embedding in ingestion_service.py"""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"
        from ingestion_service import IngestionService
        self.service = IngestionService()

    @patch("requests.post")
    def test_batch_embedding_success(self, mock_post):
        fake_embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "embeddings": [{"values": emb} for emb in fake_embeddings]
            },
        )

        result = self.service._generate_embeddings_batch(["text1", "text2", "text3"])
        self.assertEqual(len(result), 3)
        self.assertEqual(len(result[0]), 768)

    def test_batch_embedding_empty_input(self):
        result = self.service._generate_embeddings_batch([])
        self.assertEqual(result, [])


class TestProcessorEscalation(unittest.TestCase):
    """Tests for escalation detection in processor.py"""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    @patch("ai.llm_client.requests.post")
    @patch("jira_service.JiraService.create_ticket")
    def test_escalation_detected_by_marker(self, mock_jira, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "[ESCALATE] ขอส่งต่อเจ้าหน้าที่"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )
        mock_jira.return_value = {"key": "CS-123"}

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="ช่วยด้วย",
            history=[],
        )

        self.assertTrue(result["should_escalate"])
        self.assertNotIn("[ESCALATE]", result["message"])

    @patch("ai.llm_client.requests.post")
    def test_no_escalation_normal_response(self, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "สวัสดีครับ ยินดีช่วยเหลือ"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="สวัสดี",
            history=[],
        )

        self.assertFalse(result["should_escalate"])
        self.assertIn("สวัสดี", result["message"])

    @patch("ai.llm_client.requests.post")
    def test_escalation_detected_by_thai_keyword(self, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "ส่งต่อปัญหานี้ให้เจ้าหน้าที่ดูแลครับ"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="ปัญหาเงิน",
            history=[],
        )

        self.assertTrue(result["should_escalate"])


class TestProcessorMarkdownCleaning(unittest.TestCase):
    """Tests for markdown removal (LINE compatibility)."""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    @patch("ai.llm_client.requests.post")
    def test_markdown_stripped(self, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "**Bold text** and *italic* and ## Header"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="test",
            history=[],
        )

        self.assertNotIn("**", result["message"])
        self.assertNotIn("##", result["message"])
        self.assertIn("Bold text", result["message"])


class TestCacheLayer(unittest.TestCase):
    """Tests for app/cache.py in-memory mode."""

    def setUp(self):
        from app.cache import _memory_cache
        _memory_cache.clear()

    def test_set_and_get(self):
        from app.cache import cache_set, cache_get

        cache_set("test", "key1", {"data": "hello"}, ttl_seconds=60)
        result = cache_get("test", "key1")
        self.assertEqual(result, {"data": "hello"})

    def test_expired_entry(self):
        from app.cache import cache_set, cache_get

        cache_set("test", "key2", "value", ttl_seconds=-1)  # Already expired
        result = cache_get("test", "key2")
        self.assertIsNone(result)

    def test_cache_delete(self):
        from app.cache import cache_set, cache_get, cache_delete

        cache_set("test", "key3", "value", ttl_seconds=60)
        cache_delete("test", "key3")
        result = cache_get("test", "key3")
        self.assertIsNone(result)

    def test_embedding_cache(self):
        from app.cache import set_cached_embedding, get_cached_embedding

        fake_embedding = [0.1] * 768
        set_cached_embedding("test query", fake_embedding)
        result = get_cached_embedding("test query")
        self.assertEqual(result, fake_embedding)

    def test_bot_config_cache(self):
        from app.cache import set_bot_config, get_bot_config, invalidate_bot_config

        config = {"name": "TestBot", "system_prompt": "Hello"}
        set_bot_config("bot-123", config)
        self.assertEqual(get_bot_config("bot-123"), config)

        invalidate_bot_config("bot-123")
        self.assertIsNone(get_bot_config("bot-123"))


class TestIntentClassifier(unittest.TestCase):
    """Tests for ai/intent_classifier.py"""

    def setUp(self):
        from ai.intent_classifier import IntentClassifier
        self.classifier = IntentClassifier()

    def test_greeting_detected(self):
        result = self.classifier.classify("สวัสดีครับ")
        self.assertEqual(result.intent, "greeting")
        self.assertFalse(result.requires_rag)
        self.assertEqual(result.model_tier, "fast")

    def test_greeting_english(self):
        result = self.classifier.classify("Hello there")
        self.assertEqual(result.intent, "greeting")

    def test_escalation_detected(self):
        result = self.classifier.classify("ขอคุยกับเจ้าหน้าที่หน่อย ติดต่อเจ้าหน้าที่")
        self.assertEqual(result.intent, "escalation")
        self.assertFalse(result.requires_rag)

    def test_complaint_detected(self):
        result = self.classifier.classify("เงินหาย ไม่พอใจมาก")
        self.assertEqual(result.intent, "complaint")
        self.assertTrue(result.requires_rag)
        self.assertEqual(result.model_tier, "quality")

    def test_thanks_detected(self):
        result = self.classifier.classify("ขอบคุณครับ")
        self.assertEqual(result.intent, "thanks")
        self.assertFalse(result.requires_rag)

    def test_faq_default(self):
        result = self.classifier.classify("วิธีเปลี่ยนรหัสผ่าน")
        self.assertEqual(result.intent, "faq")
        self.assertTrue(result.requires_rag)

    def test_complex_query_uses_quality_tier(self):
        result = self.classifier.classify(
            "ช่วยเปรียบเทียบแพ็คเกจ A กับ B ว่าอันไหนดีกว่า อธิบายรายละเอียดด้วย"
        )
        self.assertEqual(result.model_tier, "quality")

    def test_short_query_uses_fast_tier(self):
        result = self.classifier.classify("ราคาเท่าไหร่")
        self.assertEqual(result.model_tier, "fast")


class TestModelRouter(unittest.TestCase):
    """Tests for ai/model_router.py"""

    def setUp(self):
        from ai.model_router import ModelRouter
        self.router = ModelRouter(api_key="test-key")

    def test_default_model(self):
        client = self.router.get_client()
        self.assertEqual(client.model, "gemini-2.0-flash")

    def test_fast_intent_routes_to_flash(self):
        from ai.intent_classifier import IntentResult
        intent = IntentResult(intent="greeting", confidence=0.9, requires_rag=False, model_tier="fast")
        client = self.router.get_client(intent=intent)
        self.assertEqual(client.model, "gemini-2.0-flash")

    def test_quality_intent_routes_to_pro(self):
        from ai.intent_classifier import IntentResult
        intent = IntentResult(intent="complaint", confidence=0.9, requires_rag=True, model_tier="quality")
        client = self.router.get_client(intent=intent)
        self.assertEqual(client.model, "gemini-2.5-flash")

    def test_bot_config_override(self):
        import json
        config = json.dumps({"model": "gemini-2.0-flash-lite"})
        client = self.router.get_client(bot_model_config=config)
        self.assertEqual(client.model, "gemini-2.0-flash-lite")

    def test_client_caching(self):
        client1 = self.router.get_client()
        client2 = self.router.get_client()
        self.assertIs(client1, client2)

    def test_model_info(self):
        from ai.intent_classifier import IntentResult
        intent = IntentResult(intent="faq", confidence=0.7, requires_rag=True, model_tier="fast")
        info = self.router.get_model_info(intent=intent)
        self.assertEqual(info["reason"], "intent")
        self.assertIn("model", info)


class TestQualityGuard(unittest.TestCase):
    """Tests for ai/quality_guard.py"""

    def setUp(self):
        from ai.quality_guard import QualityGuard
        self.guard = QualityGuard()

    def test_clean_response_passes(self):
        result = self.guard.check("สวัสดีครับ ยินดีช่วยเหลือ")
        self.assertTrue(result.passed)
        self.assertEqual(len(result.issues), 0)

    def test_markdown_cleaned(self):
        result = self.guard.check("**Bold** and *italic* and ## Header")
        self.assertNotIn("**", result.cleaned_response)
        self.assertNotIn("##", result.cleaned_response)
        self.assertIn("Bold", result.cleaned_response)

    def test_too_short_response(self):
        result = self.guard.check("OK")
        self.assertIn("response_too_short", result.issues)

    def test_api_key_leak_detected(self):
        result = self.guard.check("Use key AIzaSyD1234567890abcdefghijklmnopqrstuvwxyz")
        self.assertIn("leaked_api_key", result.issues)
        self.assertFalse(result.passed)

    def test_long_response_truncated(self):
        long_text = "ก" * 5000
        result = self.guard.check(long_text)
        self.assertTrue(len(result.cleaned_response) <= 4503)  # 4500 + "..."
        self.assertIn("response_truncated", result.issues)

    def test_repetition_detected(self):
        repeated = "This is a test sentence for checking.\n" * 5
        result = self.guard.check(repeated)
        self.assertIn("repetition_removed", result.issues)

    def test_hallucination_no_context(self):
        result = self.guard.check("ตามข้อมูลที่มี ราคาคือ 500 บาท", rag_context="", query="ราคา")
        self.assertIn("potential_hallucination", result.issues)


class TestToolExecutor(unittest.TestCase):
    """Tests for ai/tools.py"""

    def setUp(self):
        from ai.tools import ToolExecutor
        self.executor = ToolExecutor()

    def test_business_hours(self):
        result = self.executor.execute("get_business_hours", {})
        self.assertIn("result", result)
        self.assertIn("เวลาทำการ", result["result"])

    def test_unknown_tool(self):
        result = self.executor.execute("nonexistent_tool", {})
        self.assertIn("error", result)

    def test_search_without_services(self):
        result = self.executor.execute("search_knowledge_base", {"query": "test"})
        self.assertIn("result", result)

    def test_create_ticket_without_jira(self):
        result = self.executor.execute("create_support_ticket", {"summary": "Test issue"})
        self.assertIn("result", result)

    def test_gemini_tools_config_format(self):
        config = self.executor.get_gemini_tools_config()
        self.assertIsInstance(config, list)
        self.assertTrue(len(config) > 0)
        self.assertIn("function_declarations", config[0])


class TestFunctionCallingClient(unittest.TestCase):
    """Tests for function calling in ai/llm_client.py"""

    def setUp(self):
        from ai.llm_client import GeminiRESTClient
        self.client = GeminiRESTClient(api_key="test-key", model="gemini-2.0-flash")

    @patch("ai.llm_client.requests.post")
    def test_generate_with_tools_text_response(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "Hello!"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )
        tools = [{"function_declarations": []}]
        result = self.client.generate_with_tools("Say hello", tools)
        self.assertEqual(result["type"], "text")
        self.assertEqual(result["content"], "Hello!")

    @patch("ai.llm_client.requests.post")
    def test_generate_with_tools_function_call(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [
                    {"functionCall": {"name": "search_knowledge_base", "args": {"query": "password reset"}}}
                ]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )
        tools = [{"function_declarations": []}]
        result = self.client.generate_with_tools("How to reset password?", tools)
        self.assertEqual(result["type"], "function_call")
        self.assertEqual(result["name"], "search_knowledge_base")
        self.assertEqual(result["args"]["query"], "password reset")

    @patch("ai.llm_client.requests.post")
    def test_generate_with_tool_result(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "To reset your password, go to Settings."}]}}],
                "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 10, "totalTokenCount": 30},
            },
        )
        tools = [{"function_declarations": []}]
        result = self.client.generate_with_tool_result(
            "How to reset?", "search_knowledge_base", {"query": "reset"},
            {"result": "Go to Settings > Password"}, tools
        )
        self.assertIn("reset", result.lower())


class TestProcessorWithIntentRouting(unittest.TestCase):
    """Tests for processor.py with intent classification and model routing."""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    @patch("ai.llm_client.requests.post")
    def test_greeting_skips_rag(self, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "สวัสดีครับ ยินดีช่วยเหลือ"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="สวัสดีครับ",
            history=[],
        )

        self.assertEqual(result["intent"], "greeting")
        self.assertIn("สวัสดี", result["message"])

    @patch("ai.llm_client.requests.post")
    def test_escalation_intent_forces_escalation(self, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "ขอส่งต่อให้เจ้าหน้าที่ดูแลครับ"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="ขอคุยกับเจ้าหน้าที่ ติดต่อเจ้าหน้าที่",
            history=[],
        )

        self.assertTrue(result["should_escalate"])
        self.assertEqual(result["intent"], "escalation")

    @patch("ai.llm_client.requests.post")
    def test_model_used_field_present(self, mock_post):
        from processor import Processor

        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "ตอบกลับ"}]}}],
                "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5, "totalTokenCount": 15},
            },
        )

        processor = Processor()
        result = processor.process_message(
            user_id="user123",
            content="test",
            history=[],
        )

        self.assertIn("model_used", result)
        self.assertIn("intent", result)


if __name__ == "__main__":
    unittest.main()
