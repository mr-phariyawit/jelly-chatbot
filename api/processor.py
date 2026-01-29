"""
IT Support Message Processor
Orchestrates AI services (LLM, RAG, Vision, Memory, Intent, Tools) for processing support requests.
Delegates to modular services in ai/ package.
"""

import os
import re
import logging
import time
import uuid
import json as json_module
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import File, Bot, BotLog, FileChunk
from jira_service import JiraService
from utils import sanitize_text
from ai.llm_client import GeminiRESTClient
from ai.rag_service import RAGService
from ai.vision_service import VisionService
from ai.memory_service import MemoryService
from ai.intent_classifier import IntentClassifier
from ai.model_router import ModelRouter
from ai.quality_guard import QualityGuard
from ai.tools import ToolExecutor

logger = logging.getLogger(__name__)

# Default System Prompt (Generic - can be customized per bot)
SYSTEM_PROMPT = """คุณคือ AI Assistant ที่ช่วยเหลือผู้ใช้งาน

⚠️ กฎสำคัญในการตอบ:
• ห้ามใช้ markdown เช่น **, ##, - bullet ให้ใช้ข้อความธรรมดา
• ใช้ emoji ได้แต่ต้องสุภาพและ professional เช่ ✅ ❌ 📱 💡 🔧
• ใช้ขึ้นบรรทัดใหม่แทนการใช้ bullet points
• ตอบสั้นกระชับ เข้าใจง่าย

🚨 กรณีที่ต้องส่งต่อเจ้าหน้าที่ (ตอบด้วย [ESCALATE]):
• ผู้ใช้พูดว่า "อยากติดต่อเจ้าหน้าที่" หรือ "ขอคุยกับคน"
• ปัญหาที่คุณไม่รู้วิธีแก้ไข
• เรื่องเงินหรือธุรกรรมผิดพลาด

เมื่อต้องส่งต่อ ให้ขึ้นต้นข้อความด้วย [ESCALATE] ตามด้วยสรุปปัญหาสั้นๆ"""


def log_bot_event(db: Session, bot_id: str, level: str, event_type: str, message: str, metadata: dict = None):
    """Helper to log bot events to database"""
    try:
        clean_message = sanitize_text(message)
        clean_metadata = None
        if metadata:
            json_str = json_module.dumps(metadata, ensure_ascii=False)
            clean_metadata = sanitize_text(json_str)

        log_entry = BotLog(
            id=str(uuid.uuid4()),
            bot_id=bot_id,
            level=level,
            event_type=event_type,
            message=clean_message,
            log_metadata=clean_metadata,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log bot event: {e}")


class Processor:
    """Main processor orchestrating LLM, RAG, Vision, Memory, Intent, and Tools."""

    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            self.gemini = GeminiRESTClient(self.gemini_key, "gemini-2.0-flash")
            logger.info("Gemini REST client initialized")
        else:
            logger.warning("GEMINI_API_KEY not set")
            self.gemini = None

        self.rag = RAGService(self.gemini)
        self.vision = VisionService(self.gemini)
        self.memory = MemoryService(self.gemini)
        self.intent_classifier = IntentClassifier(self.gemini)
        self.quality_guard = QualityGuard(self.gemini)
        self.jira_service = JiraService()

        # Model router and tool executor
        if self.gemini_key:
            self.model_router = ModelRouter(self.gemini_key)
        else:
            self.model_router = None
        self.tool_executor = ToolExecutor(
            rag_service=self.rag,
            jira_service=self.jira_service,
        )

    def create_jira_ticket(self, summary: str, description: str, system: str = "General") -> Optional[str]:
        """Create a Jira ticket for escalation."""
        try:
            match = re.search(r"User ID: (\S+)", description)
            user_id_val = match.group(1) if match else "Unknown"
            result = self.jira_service.create_ticket(summary, description, user_id_val)
            return result['key'] if result else None
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return None

    def _search_knowledge_base(self, db: Session, bot_id: str, query: str) -> str:
        """Search knowledge base using hybrid RAG service."""
        return self.rag.search(db, bot_id, query)

    def _fetch_knowledge_base_legacy(self, db: Session, bot_id: str) -> str:
        """Fallback: fetch all text content."""
        return self.rag._fetch_legacy(db, bot_id)

    def process_image(self, user_id: str, image_content: bytes, db: Session, bot_id: str) -> Dict[str, Any]:
        """Process image message using Vision + RAG."""
        logger.info(f"Processing image for Bot {bot_id}, user {user_id}")

        if not self.gemini:
            return {"message": "AI not ready", "should_escalate": False}

        try:
            # 1. Analyze image
            image_analysis = self.vision.analyze_image(image_content)

            # 2. RAG search based on analysis
            rag_context = self._search_knowledge_base(db, bot_id, image_analysis)

            # 3. Generate response with RAG context
            result = self.vision.process_image_with_rag(image_content, rag_context)
            return result
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                "message": "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลรูปภาพ",
                "should_escalate": True
            }

    def process_message(
        self, user_id: str, content: str, history: List[Dict[str, str]],
        db: Session = None, bot_id: str = None, session_id: str = None
    ) -> Dict[str, Any]:
        """
        Process user message with full AI pipeline:
        1. Intent Classification → determines routing
        2. Model Selection → picks appropriate model
        3. Conversation Memory → context with summarization
        4. RAG Search → knowledge base (if needed by intent)
        5. Function Calling → structured tool use (if model requests)
        6. Quality Guard → validate response before sending
        7. Escalation Detection → create tickets if needed
        """
        start_time = time.time()
        logger.info(f"Processing message for Bot ID: {bot_id}, user: {user_id}")

        if not self.gemini:
            return {
                "message": "ขออภัยค่ะ ระบบ AI ไม่พร้อมใช้งานในขณะนี้ (Missing API Key)",
                "should_escalate": False
            }

        # --- 1. Intent Classification ---
        intent = self.intent_classifier.classify(content, history)
        logger.info(f"Intent: {intent.intent} (confidence={intent.confidence:.2f}, tier={intent.model_tier})")

        # --- 2. Model Selection ---
        bot_model_config = None
        effective_system_prompt = SYSTEM_PROMPT
        if db and bot_id:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if bot:
                if bot.system_prompt:
                    effective_system_prompt = bot.system_prompt
                bot_model_config = bot.model_config

        llm_client = self.gemini
        model_info = {"model": self.gemini.model, "tier": "default", "reason": "default"}
        if self.model_router:
            llm_client = self.model_router.get_client(intent, bot_model_config)
            model_info = self.model_router.get_model_info(intent, bot_model_config)

        if db and bot_id:
            log_bot_event(db, bot_id, "INFO", "INTENT", f"Intent: {intent.intent}", {
                "intent": intent.intent,
                "confidence": intent.confidence,
                "model": model_info["model"],
                "model_reason": model_info["reason"],
            })

        # --- 3. Conversation Memory ---
        context_str = ""
        if session_id and db:
            conv_context = self.memory.get_conversation_context(db, session_id)
            context_str = self.memory.format_context_for_prompt(conv_context)
        elif history:
            context_str = "\n".join([
                f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
                for m in history
            ])

        # --- 4. RAG Search (only if intent requires it) ---
        knowledge_context = ""
        rag_start = time.time()
        if intent.requires_rag and db and bot_id:
            knowledge_context = self._search_knowledge_base(db, bot_id, content)
            if knowledge_context:
                knowledge_context = f"\n\nข้อมูลเพิ่มเติมจากฐานความรู้ (Knowledge Base):\n{knowledge_context}"
                log_bot_event(db, bot_id, "INFO", "RAG_SEARCH", f"Found context for: {content[:50]}...", {
                    "query_preview": content[:100],
                    "context_length": len(knowledge_context),
                    "latency_ms": round((time.time() - rag_start) * 1000, 2),
                    "skipped": False,
                })
        elif not intent.requires_rag:
            logger.info(f"RAG skipped for intent: {intent.intent}")

        # --- 5. Build Prompt ---
        prompt = f"""{effective_system_prompt}

{knowledge_context}

{f"บทสนทนาที่ผ่านมา:{chr(10)}{context_str}" if context_str else ""}

คำถามล่าสุด: {content}

กรุณาตอบในฐานะ AI Support Assistant โดยใช้ข้อมูลจาก "ฐานความรู้ (Knowledge Base)" ด้านบนในการตอบคำถามได้เลย (ถ้ามีข้อมูลที่ตรงกัน):"""

        try:
            # --- 6. Generate LLM Response (with optional function calling) ---
            llm_start = time.time()
            ai_text = self._generate_with_tools(
                llm_client, prompt, db=db, bot_id=bot_id, user_id=user_id
            )
            llm_latency = round((time.time() - llm_start) * 1000, 2)

            if db and bot_id:
                log_bot_event(db, bot_id, "INFO", "LLM_CALL", f"Generated response for: {content[:50]}...", {
                    "model": model_info["model"],
                    "intent": intent.intent,
                    "prompt_length": len(prompt),
                    "response_length": len(ai_text),
                    "latency_ms": llm_latency,
                })

            # --- 7. Quality Guard ---
            quality = self.quality_guard.check(ai_text, knowledge_context, content)
            ai_text = quality.cleaned_response

            if quality.issues and db and bot_id:
                log_bot_event(db, bot_id, "WARN", "QUALITY", f"Quality issues: {quality.issues}", {
                    "issues": quality.issues,
                    "confidence": quality.confidence_score,
                })

            # --- 8. Escalation Detection ---
            should_escalate = '[ESCALATE]' in ai_text
            if not should_escalate:
                keywords = ['ส่งต่อปัญหานี้ให้เจ้าหน้าที่', 'ส่งต่อให้เจ้าหน้าที่', 'โปรดรอการติดต่อจากเจ้าหน้าที่']
                if any(k in ai_text for k in keywords):
                    should_escalate = True

            # Intent-based escalation
            if intent.intent == "escalation":
                should_escalate = True

            final_message = ai_text.replace('[ESCALATE]', '').strip()

            # --- 9. Create JIRA Ticket if Escalated ---
            ticket_key = None
            if should_escalate:
                ticket_key = self.create_jira_ticket(
                    summary=f"Escalation from User {user_id[:8]}...",
                    description=f"User ID: {user_id}\n\nLast Message: {content}\n\nContext:\n{context_str}",
                    system="AI-Support"
                )
                if ticket_key and db and bot_id:
                    log_bot_event(db, bot_id, "INFO", "JIRA", f"Created ticket: {ticket_key}", {
                        "ticket_key": ticket_key,
                        "user_id": user_id
                    })
                if ticket_key:
                    final_message += f"\n\n(Ticket: {ticket_key})"

            total_latency = round((time.time() - start_time) * 1000, 2)
            logger.info(f"Message processed in {total_latency}ms (intent={intent.intent}, model={model_info['model']})")

            return {
                "message": final_message,
                "should_escalate": should_escalate,
                "ticket_key": ticket_key,
                "intent": intent.intent,
                "model_used": model_info["model"],
            }

        except Exception as e:
            logger.error(f"AI Processing Error: {e}")
            if db and bot_id:
                log_bot_event(db, bot_id, "ERROR", "ERROR", f"AI processing failed: {str(e)}", {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "user_message": content[:100]
                })
            return {
                "message": "ขออภัยค่ะ เกิดข้อผิดพลาดในการประมวลผล",
                "should_escalate": True
            }

    def _generate_with_tools(
        self, llm_client: GeminiRESTClient, prompt: str,
        db: Session = None, bot_id: str = None, user_id: str = None
    ) -> str:
        """
        Generate response with function calling support.
        If the model requests a tool call, execute it and continue generation.
        """
        tools_config = self.tool_executor.get_gemini_tools_config()

        try:
            result = llm_client.generate_with_tools(prompt, tools_config)

            if result["type"] == "text":
                return result["content"].strip()

            if result["type"] == "function_call":
                tool_name = result["name"]
                tool_args = result["args"]
                logger.info(f"Function call: {tool_name}({tool_args})")

                # Execute the tool
                tool_result = self.tool_executor.execute(
                    tool_name, tool_args,
                    db=db, bot_id=bot_id, user_id=user_id,
                )

                if db and bot_id:
                    log_bot_event(db, bot_id, "INFO", "TOOL_CALL", f"Tool: {tool_name}", {
                        "tool": tool_name,
                        "args": tool_args,
                        "result_preview": str(tool_result)[:200],
                    })

                # Continue generation with tool result
                final_text = llm_client.generate_with_tool_result(
                    prompt, tool_name, tool_args, tool_result, tools_config
                )
                return final_text.strip()

        except Exception as e:
            logger.warning(f"Function calling failed, falling back to standard generation: {e}")
            # Fallback to standard generation without tools
            return llm_client.generate_content(prompt).strip()

    def generate_system_prompt_suggestion(self, db: Session, bot_id: str) -> str:
        """Analyze all files in Knowledge Base and suggest a System Prompt."""
        if not self.gemini:
            return "Error: AI not configured."

        try:
            from models import File as DBFile
            files = db.query(DBFile).filter(DBFile.bot_id == bot_id).all()

            if not files:
                return "Error: No files found to generate a prompt. Please upload files first."

            file_prompts = []
            for f in files:
                if f.description:
                    file_prompts.append(f"- File '{f.filename}': {f.description}")
                else:
                    snippet = f.content[:200].replace('\n', ' ') if f.content else "No content"
                    file_prompts.append(f"- File '{f.filename}': (Unverified Content) {snippet}...")

            aggregated_context = "\n".join(file_prompts)

            meta_prompt = f"""
            Task: Create a robust "System Prompt" for an AI Assistant based on the provided File Contexts.

            The user has defined specific purposes for each file in the knowledge base. Use these to construct a cohesive persona and instruction set.

            File Contexts:
            {aggregated_context}

            Instructions:
            1. Analyze the file contexts to understand the domain.
            2. Define a Persona: "You are an AI assistant for [Organization/Context]..."
            3. Define Rules:
               - Scope of operation based on available files.
               - Tone of voice (Formal, Friendly, etc.).
               - STRICTLY rely on the knowledge base.
            4. Output ONLY the System Prompt text.
            5. Use Thai Language.
            """

            return self.gemini.generate_content(meta_prompt)

        except Exception as e:
            logger.error(f"Prompt generation failed: {e}")
            return f"Error computing prompt: {str(e)}"

    def _extract_content_from_gcs(self, gcs_uri: str, content_type: str = None) -> str:
        """Download file from GCS and extract text content (first 3 pages for PDFs)."""
        from google.cloud import storage
        import io

        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")

        parts = gcs_uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""

        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content_bytes = blob.download_as_bytes()

        if not content_type:
            if blob_name.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif blob_name.lower().endswith('.txt'):
                content_type = 'text/plain'

        if content_type and 'pdf' in content_type.lower():
            text = ""
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content_bytes))
                max_pages = min(3, len(reader.pages))
                for i in range(max_pages):
                    extracted = reader.pages[i].extract_text()
                    if extracted:
                        text += f"--- Page {i+1} ---\n{extracted}\n"
            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")

            if len(text) < 100:
                try:
                    import google.generativeai as genai
                    if self.gemini and self.gemini.api_key:
                        genai.configure(api_key=self.gemini.api_key)
                        model = genai.GenerativeModel("gemini-2.0-flash")
                        response = model.generate_content([
                            {'mime_type': 'application/pdf', 'data': content_bytes},
                            "Extract text from this document for summarization."
                        ])
                        return response.text[:15000]
                except Exception as e:
                    logger.error(f"OCR failed: {e}")

            return text[:15000]
        else:
            try:
                return content_bytes.decode('utf-8')[:15000]
            except UnicodeDecodeError:
                return content_bytes.decode('latin-1')[:15000]

    def generate_file_summary(self, db: Session, file_id: str) -> str:
        """Analyze a file and generate a short description/context summary."""
        if not self.gemini:
            return "Error: AI not configured."

        try:
            from models import File as DBFile
            start_time = time.time()

            file_record = db.query(DBFile).filter(DBFile.id == file_id).first()
            if not file_record:
                return "Error: File not found."

            content_snippet = None

            if file_record.gcs_uri and file_record.gcs_uri.startswith("gs://"):
                try:
                    content_snippet = self._extract_content_from_gcs(file_record.gcs_uri, file_record.content_type)
                except Exception as e:
                    logger.warning(f"GCS extraction failed: {e}")

            if not content_snippet or content_snippet == "[Stored in GCS]":
                db_content = db.query(func.substr(DBFile.content, 1, 15000)).filter(DBFile.id == file_id).scalar()
                if db_content and db_content != "[Stored in GCS]":
                    content_snippet = db_content

            if not content_snippet:
                chunks = db.query(FileChunk.content).filter(FileChunk.file_id == file_id)\
                           .order_by(FileChunk.chunk_index.asc()).limit(5).all()
                if chunks:
                    content_snippet = "\n".join([c[0] for c in chunks])

            if not content_snippet:
                return "Error: File content not found or empty."

            meta_prompt = f"""
            Task: Analyze the following document and generate a "File Context Prompt" (max 2 sentences).

            This output will be used as a specific instruction for an AI Agent on how to use this file.

            Format: "Use this file for [topics/purpose]. Key information includes [key entities/rules]."
            Example: "Use this file for answering questions about HR Leave Policy. Key information includes sick leave quotas, vacation approval workflows, and remote work guidelines."

            Document Content (Snippet):
            {content_snippet[:12000]}

            Output ONLY the File Context Prompt in Thai language.
            """

            suggestion = self.gemini.generate_content(meta_prompt, timeout=120)
            logger.info(f"File analysis completed in {time.time() - start_time:.2f}s")

            return suggestion

        except Exception as e:
            logger.error(f"File summary failed: {str(e)}", exc_info=True)
            return f"Error computing summary: {str(e)}"
