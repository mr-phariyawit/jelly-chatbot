
"""
IT Support Message Processor
Main logic for processing support requests using AI (Gemini) and Jira
"""

import os
import re
import logging
import requests
from typing import Dict, Any, Optional, List

# from jira import JIRA -> Moved to jira_service
from jira_service import JiraService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiRESTClient:
    """Gemini API client using REST instead of gRPC to avoid credential issues."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

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

    def embed_content(self, text: str, task_type: str = "RETRIEVAL_QUERY") -> list:
        """Generate embeddings using REST API (using gemini-embedding-001 - stable model)."""
        # Note: text-embedding-004 was deprecated on Jan 14, 2026. Using gemini-embedding-001.
        # gemini-embedding-001 defaults to 3072 dims, but our DB has Vector(768), so we specify 768.
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

# Default System Prompt (Generic - can be customized per bot)
SYSTEM_PROMPT = """คุณคือ AI Assistant ที่ช่วยเหลือผู้ใช้งาน

⚠️ กฎสำคัญในการตอบ:
• ห้ามใช้ markdown เช่น **, ##, - bullet ให้ใช้ข้อความธรรมดา
• ใช้ emoji ได้แต่ต้องสุภาพและ professional เช่น ✅ ❌ 📱 💡 🔧
• ใช้ขึ้นบรรทัดใหม่แทนการใช้ bullet points
• ตอบสั้นกระชับ เข้าใจง่าย

🚨 กรณีที่ต้องส่งต่อเจ้าหน้าที่ (ตอบด้วย [ESCALATE]):
• ผู้ใช้พูดว่า "อยากติดต่อเจ้าหน้าที่" หรือ "ขอคุยกับคน"
• ปัญหาที่คุณไม่รู้วิธีแก้ไข
• เรื่องเงินหรือธุรกรรมผิดพลาด

เมื่อต้องส่งต่อ ให้ขึ้นต้นข้อความด้วย [ESCALATE] ตามด้วยสรุปปัญหาสั้นๆ"""

from sqlalchemy.orm import Session
from models import File, Bot, BotLog
import uuid
import json as json_module


from utils import sanitize_text

def log_bot_event(db: Session, bot_id: str, level: str, event_type: str, message: str, metadata: dict = None):
    """Helper to log bot events to database"""
    try:
        # Sanitize inputs
        clean_message = sanitize_text(message)
        clean_metadata = None
        if metadata:
            # Dump to JSON then sanitize safely
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
    def __init__(self):
        # Initialize Gemini REST Client (avoid gRPC issues)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            self.gemini = GeminiRESTClient(self.gemini_key, "gemini-2.0-flash")
            logger.info("Gemini REST client initialized")
        else:
            logger.warning("GEMINI_API_KEY not set")
            self.gemini = None

        # Initialize Jira Service
        self.jira_service = JiraService()

    def create_jira_ticket(self, summary: str, description: str, system: str = "General") -> Optional[str]:
        """Create a Jira ticket for escalation via JiraService"""
        try:
            result = self.jira_service.create_ticket(summary, description, user_id=description.split("User ID: ")[-1].split("\n")[0]) # Extract user_id hack or just pass generic?
            # Actually, the original caller passes user_id in description formatting.
            # Let's clean this up.
            # The caller passes a description like "User ID: ... \n\n ..."
            # JiraService expects (summary, description, user_id).
            # I will pass user_id="Unknown" if parsing fails, but better to fix call site.
            # For now, let's just pass the whole description as description AND user_id.
            # Wait, JiraService signature I wrote: create_ticket(summary, description, user_id)
            # logic: description = f"{description}\n\n[Reported by Line User: {user_id}]"
            # So I should pass the clean description.
            
            # Let's adjust this method to just call the service simply.
            # Caller provides (summary, description).
            # I will assume the caller puts user_id in description?
            # LINES 280-285 in original code:
            # ticket_key = self.create_jira_ticket(summary=..., description=f"User ID: {user_id}...")
            
            # So I will just pass user_id extracted or dummy.
            match = re.search(r"User ID: (\S+)", description)
            user_id_val = match.group(1) if match else "Unknown"
            
            result = self.jira_service.create_ticket(summary, description, user_id_val)
            return result['key'] if result else None
            
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return None

    def _search_knowledge_base(self, db: Session, bot_id: str, query: str) -> str:
        """Search knowledge base using Vector Similarity (if available) or full-text fallback"""
        try:
            from models import FileChunk, File
            
            # 1. Check if we have chunks for this bot
            has_chunks = db.query(FileChunk).join(File).filter(File.bot_id == bot_id).first()
            if not has_chunks:
                logger.info("No vectors found, falling back to legacy full-text")
                return self._fetch_knowledge_base_legacy(db, bot_id)

            # 2. Embed Query using REST client
            if not self.gemini:
                return ""

            query_vector = self.gemini.embed_content(query, "retrieval_query")
            
            # 3. Vector Search
            # PostGres syntax: order_by(FileChunk.embedding.cosine_distance(query_vector))
            chunks = db.query(FileChunk).join(File).filter(File.bot_id == bot_id)\
                       .order_by(FileChunk.embedding.cosine_distance(query_vector))\
                       .limit(5).all()
            
            if not chunks:
                return ""
                
            logger.info(f"Vector search found {len(chunks)} relevant chunks")
            return "\n\n".join([f"--- Context (from {c.file.filename}) ---\n{c.content}" for c in chunks])

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            # Fallback to legacy
            return self._fetch_knowledge_base_legacy(db, bot_id)

    def _fetch_knowledge_base_legacy(self, db: Session, bot_id: str) -> str:
        """Original method: Fetch all text content"""
        try:
            files = db.query(File).filter(
                File.bot_id == bot_id,
                File.content.isnot(None)
            ).all()
            
            if not files:
                return ""

            kb_content = []
            for f in files:
                if f.content:
                    kb_content.append(f"--- File: {f.filename} ---\n{f.content}")
            
            return "\n\n".join(kb_content)
        except Exception as e:
            logger.error(f"Failed to fetch knowledge base: {e}")
            return ""

    def process_image(self, user_id: str, image_content: bytes, db: Session, bot_id: str) -> Dict[str, Any]:
        """Process image message using Gemini Vision + RAG (REST API)"""
        logger.info(f"Processing image for Bot {bot_id}, user {user_id}")

        if not self.gemini:
             return {"message": "AI not ready", "should_escalate": False}

        try:
            import base64

            # 1. Vision Analysis using REST API with base64 encoded image
            vision_prompt = """
            Analyze this image. If it shows an error message or technical issue, extract the key error text and describe the problem concisely.
            If it's just a general photo, describe what it is.
            Output format: [Analysis] <description>
            """

            # Encode image to base64
            image_b64 = base64.b64encode(image_content).decode('utf-8')

            # REST API call with image
            url = f"{self.gemini.base_url}/models/{self.gemini.model}:generateContent?key={self.gemini.api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {"text": vision_prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}}
                    ]
                }]
            }

            response = requests.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                raise Exception(f"Vision API error: {response.status_code}")

            data = response.json()
            image_analysis = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            logger.info(f"Image Analysis: {image_analysis}")

            # 2. RAG Search with Analysis
            rag_context = self._search_knowledge_base(db, bot_id, image_analysis)

            # 3. Final Answer Generation
            final_prompt = f"""
            User sent an image.
            Image Analysis: {image_analysis}

            Relevant Knowledge Base Context:
            {rag_context}

            Instruction:
            Based on the image analysis and the knowledge base, provide a solution or helpful response to the user.
            If the knowledge base has a specific fix for this error, Provide it clearly.
            Response in Thai Language.
            """

            final_response = self.gemini.generate_content(final_prompt)
            return {
                "message": final_response,
                "should_escalate": "contact admin" in final_response.lower()
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                "message": "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลรูปภาพ",
                "should_escalate": True
            }

    def process_message(self, user_id: str, content: str, history: List[Dict[str, str]], db: Session = None, bot_id: str = None) -> Dict[str, Any]:
        """
        Process user message with Gemini REST API and handle escalation
        """
        import time
        start_time = time.time()
        logger.info(f"Processing message for Bot ID: {bot_id}, user: {user_id}")
        
        if not self.gemini:
            return {
                "message": "ขออภัยค่ะ ระบบ AI ไม่พร้อมใช้งานในขณะนี้ (Missing API Key)",
                "should_escalate": False
            }

        # Fetch bot's custom system prompt if available
        effective_system_prompt = SYSTEM_PROMPT
        if db and bot_id:
            bot = db.query(Bot).filter(Bot.id == bot_id).first()
            if bot and bot.system_prompt:
                effective_system_prompt = bot.system_prompt
                logger.info(f"Using custom system prompt for bot {bot_id}")

        # 1. Fetch Knowledge Base (Vector or Legacy)
        knowledge_context = ""
        rag_start = time.time()
        if db and bot_id:
            knowledge_context = self._search_knowledge_base(db, bot_id, content)
            if knowledge_context:
                knowledge_context = f"\n\nข้อมูลเพิ่มเติมจากฐานความรู้ (Knowledge Base):\n{knowledge_context}"
                # Log RAG search
                log_bot_event(db, bot_id, "INFO", "RAG_SEARCH", f"Found context for: {content[:50]}...", {
                    "query_preview": content[:100],
                    "context_length": len(knowledge_context),
                    "latency_ms": round((time.time() - rag_start) * 1000, 2)
                })

        if knowledge_context:
            logger.info(f"Injecting Knowledge Base context (len={len(knowledge_context)})")

        # Build context
        context_str = "\\n".join([f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in history])

        prompt = f"""{effective_system_prompt}

{knowledge_context}

บทสนทนาที่ผ่านมา:
{context_str}

คำถามล่าสุด: {content}

กรุณาตอบในฐานะ AI Support Assistant โดยใช้ข้อมูลจาก "ฐานความรู้ (Knowledge Base)" ด้านบนในการตอบคำถามได้เลย (ถ้ามีข้อมูลที่ตรงกัน):"""

        try:
            # Use REST API instead of gRPC SDK
            llm_start = time.time()
            ai_text = self.gemini.generate_content(prompt).strip()
            llm_latency = round((time.time() - llm_start) * 1000, 2)
            
            # Log LLM call
            if db and bot_id:
                log_bot_event(db, bot_id, "INFO", "LLM_CALL", f"Generated response for: {content[:50]}...", {
                    "model": "gemini-2.0-flash",
                    "prompt_length": len(prompt),
                    "response_length": len(ai_text),
                    "latency_ms": llm_latency
                })
            
            # Remove Markdown (Line doesn't support it)
            ai_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', ai_text)  # Bold
            ai_text = re.sub(r'\*([^*]+)\*', r'\1', ai_text)      # Italic
            ai_text = re.sub(r'#{1,6}\s', '', ai_text)            # Headers
            ai_text = re.sub(r'^[-*]\s', '• ', ai_text, flags=re.MULTILINE) # Bullets
            
            # Check for escalation
            should_escalate = '[ESCALATE]' in ai_text
            
            # Fallback escalation detection (Thai keywords)
            if not should_escalate:
                keywords = ['ส่งต่อปัญหานี้ให้เจ้าหน้าที่', 'ส่งต่อให้เจ้าหน้าที่', 'โปรดรอการติดต่อจากเจ้าหน้าที่']
                if any(k in ai_text for k in keywords):
                    should_escalate = True
            
            final_message = ai_text.replace('[ESCALATE]', '').strip()
            
            ticket_key = None
            if should_escalate:
                # Create Jira Ticket
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
            logger.info(f"Message processed in {total_latency}ms")

            return {
                "message": final_message,
                "should_escalate": should_escalate,
                "ticket_key": ticket_key
            }

        except Exception as e:
            logger.error(f"AI Processing Error: {e}")
            # Log error
            if db and bot_id:
                log_bot_event(db, bot_id, "ERROR", "ERROR", f"AI processing failed: {str(e)}", {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "user_message": content[:100]
                })
            return {
                "message": "ขออภัยค่ะ เกิดข้อผิดพลาดในการประมวลผล",
                "should_escalate": True # Fail safe to human
            }

    def generate_system_prompt_suggestion(self, db: Session, bot_id: str) -> str:
        """
        Analyze all files in the Knowledge Base and suggest a System Prompt.
        """
        if not self.gemini:
             return "Error: AI not configured."

        try:
            # 1. Fetch all File content to extract File Prompts
            kb_content = self._fetch_knowledge_base_legacy(db, bot_id) # Getting raw content just in case
            
            # Fetch File Objects to get descriptions
            from models import File as DBFile
            files = db.query(DBFile).filter(DBFile.bot_id == bot_id).all()
            
            if not files:
                return "Error: No files found to generate a prompt. Please upload files first."

            # Aggregate File Prompts
            file_prompts = []
            for f in files:
                if f.description:
                    file_prompts.append(f"- File '{f.filename}': {f.description}")
                else:
                    # Fallback if no description: use first 200 chars as hint
                    snippet = f.content[:200].replace('\n', ' ') if f.content else "No content"
                    file_prompts.append(f"- File '{f.filename}': (Unverified Content) {snippet}...")

            aggregated_context = "\n".join(file_prompts)

            # 2. Construct Meta-Prompt
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

            # 3. Generate
            suggestion = self.gemini.generate_content(meta_prompt)
            return suggestion

        except Exception as e:
            logger.error(f"Prompt generation failed: {e}")
            return f"Error computing prompt: {str(e)}"

    def _extract_content_from_gcs(self, gcs_uri: str, content_type: str = None) -> str:
        """
        Download file from GCS and extract text content.
        For PDFs, extracts only first 3 pages to avoid memory issues.
        """
        from google.cloud import storage
        import io
        
        # Parse GCS URI: gs://bucket/path/to/file
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        parts = gcs_uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""
        
        logger.info(f"Downloading from GCS: bucket={bucket_name}, blob={blob_name}")
        
        # Download blob to memory
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        content_bytes = blob.download_as_bytes()
        logger.info(f"Downloaded {len(content_bytes)} bytes from GCS")
        
        # Determine content type from extension if not provided
        if not content_type:
            if blob_name.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif blob_name.lower().endswith('.txt'):
                content_type = 'text/plain'
        
        # Extract text based on content type
        if content_type and 'pdf' in content_type.lower():
            # PDF: Extract first 3 pages only
            text = ""
            try:
                from pypdf import PdfReader
                pdf_file = io.BytesIO(content_bytes)
                reader = PdfReader(pdf_file)
                
                max_pages = min(3, len(reader.pages))
                for i in range(max_pages):
                    extracted = reader.pages[i].extract_text()
                    if extracted:
                        text += f"--- Page {i+1} ---\n{extracted}\n"
            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")
                # Fallback to OCR
            
            # OCR Fallback
            if len(text) < 100:
                 logger.info("PDF text empty/short, using Gemini OCR...")
                 try:
                     import google.generativeai as genai
                     # Use the same key as initialized in Processor
                     if self.gemini and self.gemini.api_key:
                         genai.configure(api_key=self.gemini.api_key)
                         model = genai.GenerativeModel("gemini-2.0-flash")
                         response = model.generate_content([
                            {'mime_type': 'application/pdf', 'data': content_bytes},
                            "Extract text from this document for summarization."
                         ])
                         return response.text[:15000]
                 except Exception as e:
                     logger.error(f"OCR failed in processor: {e}")
                     
            return text[:15000]
        else:
            # Text files: decode directly
            try:
                return content_bytes.decode('utf-8')[:15000]
            except UnicodeDecodeError:
                return content_bytes.decode('latin-1')[:15000]

    def generate_file_summary(self, db: Session, file_id: str) -> str:
        """
        Analyze a specific file and generate a short description/context summary.
        Uses SQL-level truncation to handle large files efficiently.
        Now supports GCS-stored files with PDF extraction.
        """
        if not self.gemini:
             logger.error("AI Analysis failed: Gemini API Key missing")
             return "Error: AI not configured."

        try:
            from models import File as DBFile
            from sqlalchemy import func
            import time
            
            start_time = time.time()
            logger.info(f"Starting analysis for file {file_id}")

            # Fetch file record to check for GCS URI
            file_record = db.query(DBFile).filter(DBFile.id == file_id).first()
            if not file_record:
                return "Error: File not found."

            content_snippet = None
            
            # Priority 1: If file has gcs_uri, download and extract from GCS
            if file_record.gcs_uri and file_record.gcs_uri.startswith("gs://"):
                logger.info(f"File stored in GCS: {file_record.gcs_uri}")
                try:
                    content_snippet = self._extract_content_from_gcs(file_record.gcs_uri, file_record.content_type)
                except Exception as e:
                    logger.warning(f"GCS extraction failed: {e}. Falling back to DB/Chunks.")
            
            # Priority 2: Try DB content (if not placeholder)
            if not content_snippet or content_snippet == "[Stored in GCS]":
                db_content = db.query(func.substr(DBFile.content, 1, 15000)).filter(DBFile.id == file_id).scalar()
                if db_content and db_content != "[Stored in GCS]":
                    content_snippet = db_content
                    logger.info(f"Using DB content. Length: {len(content_snippet)}")

            # Priority 3: Try FileChunks (for indexed files)
            if not content_snippet:
                logger.info("Content empty/null, attempting to fetch from FileChunks...")
                from models import FileChunk
                chunks = db.query(FileChunk.content).filter(FileChunk.file_id == file_id)\
                           .order_by(FileChunk.chunk_index.asc())\
                           .limit(5).all()
                if chunks:
                    content_snippet = "\n".join([c[0] for c in chunks])
                    logger.info(f"Reconstructed snippet from {len(chunks)} chunks. Length: {len(content_snippet)}")
            
            fetch_time = time.time() - start_time
            logger.info(f"Fetched snippet in {fetch_time:.2f}s. Length: {len(content_snippet) if content_snippet else 0}")

            if not content_snippet:
                 logger.error(f"Analysis failed: No content for file {file_id}")
                 return "Error: File content not found or empty."

            # Construct Meta-Prompt
            meta_prompt = f"""
            Task: Analyze the following document and generate a "File Context Prompt" (max 2 sentences).
            
            This output will be used as a specific instruction for an AI Agent on how to use this file.
            
            Format: "Use this file for [topics/purpose]. Key information includes [key entities/rules]."
            Example: "Use this file for answering questions about HR Leave Policy. Key information includes sick leave quotas, vacation approval workflows, and remote work guidelines."

            Document Content (Snippet):
            {content_snippet[:12000]}
            
            Output ONLY the File Context Prompt in Thai language.
            """

            # Generate with longer timeout
            logger.info("Sending request to Gemini...")
            llm_start = time.time()
            suggestion = self.gemini.generate_content(meta_prompt, timeout=120)
            llm_time = time.time() - llm_start
            
            logger.info(f"Gemini response received in {llm_time:.2f}s: {suggestion[:50]}...")
            
            return suggestion

        except Exception as e:
            logger.error(f"File summary failed details: {str(e)}", exc_info=True)
            return f"Error computing summary: {str(e)}"
