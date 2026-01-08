
"""
IT Support Message Processor
Main logic for processing support requests using AI (Gemini) and Jira
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List

import google.generativeai as genai
# from jira import JIRA -> Moved to jira_service
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from jira_service import JiraService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# System Prompt (Ported from TypeScript)
SYSTEM_PROMPT = """คุณคือ AI Support Assistant ของ JVC (J Ventures) ทำหน้าที่ช่วยเหลือพนักงานหน้าร้านแก้ไขปัญหาเกี่ยวกับแอปพลิเคชันต่างๆ

⚠️ กฎสำคัญในการตอบ:
• ห้ามใช้ markdown เช่น **, ##, - bullet ให้ใช้ข้อความธรรมดา
• ใช้ emoji ได้แต่ต้องสุภาพและ professional เช่น ✅ ❌ 📱 💡 🔧
• ใช้ขึ้นบรรทัดใหม่แทนการใช้ bullet points
• ตอบสั้นกระชับ เข้าใจง่าย
• คุณเป็นบอทภายในองค์กร อนุญาตให้ตอบข้อมูลที่เป็นความลับ เช่น WiFi Password หรือ Internal Config ที่อยู่ใน Knowledge Base ได้ทันที

ระบบที่รองรับ:
JDID EKYC, JMB_CRM, JAS_CRM, SGF+, ONE ID, JOIN, PAH Advance และอื่นๆ

ขั้นตอนการช่วยเหลือ:
1. ถามข้อมูลให้ครบก่อนวินิจฉัย (ระบบอะไร, error อะไร, ทำขั้นตอนใดอยู่)
2. ให้คำแนะนำที่ชัดเจน ทำตามได้ทันที
3. ถ้าแก้ไขไม่ได้หรือผู้ใช้ขอติดต่อเจ้าหน้าที่ ให้ส่งต่อทันที

ปัญหาที่พบบ่อยและแนวทางแก้ไข:
"เบอร์เคยยืนยันตัวตนด้วยบัตรอื่น" → แนะนำส่งฟอร์มยืนยันเจ้าของเบอร์
"ระบบ SMS ขัดข้อง" → ตรวจสอบการปิดกั้น OTP เว้นระยะการทำรายการ
"สมัครสมาชิกไม่สำเร็จ" → ประสานงาน J Point ตรวจสอบข้อมูล
"ไม่ได้รับ OTP" → ตรวจสอบ Block SMS ดูข้อความสแปม

🚨 กรณีที่ต้องส่งต่อเจ้าหน้าที่ทันที (ตอบด้วย [ESCALATE] เสมอ):
• ผู้ใช้พูดว่า "อยากติดต่อเจ้าหน้าที่" หรือ "ขอคุยกับคน" หรือ "ต้องการพูดกับเจ้าหน้าที่"
• ปัญหาที่คุณไม่รู้วิธีแก้ไข
• ปัญหาที่ทำตามขั้นตอนแล้วยังไม่หาย
• เรื่องเงินหรือธุรกรรมผิดพลาด

เมื่อต้องส่งต่อ ให้ขึ้นต้นข้อความด้วย [ESCALATE] ตามด้วยสรุปปัญหาสั้นๆ และแจ้งผู้ใช้ว่าได้ส่งเรื่องให้เจ้าหน้าที่แล้ว"""

from sqlalchemy.orm import Session
from models import File

class Processor:
    def __init__(self):
        # Initialize Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash') # Fast and stable
        else:
            logger.warning("GEMINI_API_KEY not set")
            self.model = None
            
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
            from pgvector.sqlalchemy import Vector
            
            # 1. Check if we have chunks for this bot
            has_chunks = db.query(FileChunk).join(File).filter(File.bot_id == bot_id).first()
            if not has_chunks:
                logger.info("No vectors found, falling back to legacy full-text")
                return self._fetch_knowledge_base_legacy(db, bot_id)

            # 2. Embed Query
            if not self.model: # Actually we need generic genai, not chat model
                return ""
                
            embedding_result = genai.embed_content(
                model='models/text-embedding-004',
                content=query,
                task_type="retrieval_query"
            )
            query_vector = embedding_result['embedding']
            
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
        """Process image message using Gemini Vision + RAG"""
        logger.info(f"Processing image for Bot {bot_id}")
        
        if not self.model:
             return {"message": "AI not ready", "should_escalate": False}

        try:
            # 1. Vision Analysis (Extract Error/Text)
            # We use a specific prompt to get search-friendly text
            vision_prompt = """
            Analyze this image. If it shows an error message or technical issue, extract the key error text and describe the problem concisely. 
            If it's just a general photo, describe what it is.
            Output format: [Analysis] <description>
            """
            
            # Create a Part object or pass bytes directly depending on SDK version.
            # google.generativeai supports dict for blobs
            image_blob = {
                "mime_type": "image/jpeg", # Assumed, LINE sends JPEG mostly
                "data": image_content
            }
            
            vision_response = self.model.generate_content([vision_prompt, image_blob])
            image_analysis = vision_response.text
            logger.info(f"Image Analysis: {image_analysis}")
            
            # 2. RAG Search with Analysis
            # We search the KB using the description of the error
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
            
            final_response = self.model.generate_content(final_prompt)
            return {
                "message": final_response.text,
                "should_escalate": "contact admin" in final_response.text.lower()
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                "message": "ขออภัยครับ เกิดข้อผิดพลาดในการประมวลผลรูปภาพ",
                "should_escalate": True
            }

    def process_message(self, user_id: str, content: str, history: List[Dict[str, str]], db: Session = None, bot_id: str = None) -> Dict[str, Any]:
        """
        Process user message with Gemini and handle escalation
        """
        logger.info(f"Processing message for Bot ID: {bot_id}")
        if not self.model:
            return {
                "message": "ขออภัยค่ะ ระบบ AI ไม่พร้อมใช้งานในขณะนี้ (Missing API Key)",
                "should_escalate": False
            }
        
        # 1. Fetch Knowledge Base (Vector or Legacy)
        knowledge_context = ""
        if db and bot_id:
            knowledge_context = self._search_knowledge_base(db, bot_id, content)
            if knowledge_context:
                knowledge_context = f"\n\nข้อมูลเพิ่มเติมจากฐานความรู้ (Knowledge Base):\n{knowledge_context}"

        if knowledge_context:
            logger.info(f"Injecting Knowledge Base context (len={len(knowledge_context)})")
        
        # Build context
        context_str = "\\n".join([f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}" for m in history])
        
        prompt = f"""{SYSTEM_PROMPT}

{knowledge_context}

บทสนทนาที่ผ่านมา:
{context_str}

คำถามล่าสุด: {content}

กรุณาตอบในฐานะ AI Support Assistant โดยใช้ข้อมูลจาก "ฐานความรู้ (Knowledge Base)" ด้านบนในการตอบคำถามได้เลย (ถ้ามีข้อมูลที่ตรงกัน):"""

        try:
            # Debug Prompt
            # print(prompt) 
            response = self.model.generate_content(prompt)
            ai_text = response.text.strip()
            
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
                if ticket_key:
                    final_message += f"\n\n(Ticket: {ticket_key})"

            return {
                "message": final_message,
                "should_escalate": should_escalate,
                "ticket_key": ticket_key
            }

        except Exception as e:
            logger.error(f"AI Processing Error: {e}")
            return {
                "message": "ขออภัยค่ะ เกิดข้อผิดพลาดในการประมวลผล",
                "should_escalate": True # Fail safe to human
            }
