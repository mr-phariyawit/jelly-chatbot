
"""
IT Support Message Processor
Main logic for processing support requests using AI (Gemini) and Jira
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from jira import JIRA
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage

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
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp') # Use latest available
        else:
            logger.warning("GEMINI_API_KEY not set")
            self.model = None

    def _get_jira_client(self):
        """Initialize Jira client on demand to handle dynamic creds if needed"""
        jira_url = os.getenv("JIRA_URL", "https://jventures.atlassian.net")
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_API_TOKEN")
        
        if not (jira_email and jira_token):
            return None
            
        return JIRA(server=jira_url, basic_auth=(jira_email, jira_token))

    def create_jira_ticket(self, summary: str, description: str, system: str = "General") -> Optional[str]:
        """Create a Jira ticket for escalation"""
        try:
            jira = self._get_jira_client()
            if not jira:
                logger.error("Jira credentials missing")
                return None

            issue_dict = {
                'project': {'key': os.getenv("JIRA_PROJECT_KEY", "CS")},
                'summary': summary,
                'description': description,
                'issuetype': {'name': 'Task'},
                'labels': ['from-line-bot', system],
            }
            
            new_issue = jira.create_issue(fields=issue_dict)
            logger.info(f"Created Jira ticket: {new_issue.key}")
            return new_issue.key
            
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return None

    def _fetch_knowledge_base(self, db: Session, bot_id: str) -> str:
        """Fetch and concatenate text content from bot's knowledge base files"""
        try:
            files = db.query(File).filter(
                File.bot_id == bot_id,
                File.content.isnot(None)
            ).all()
            
            if not files:
                return ""

            kb_content = []
            for f in files:
                # Basic check for text content based on content_type or filename
                # In main.py upload, we already filter/decode text/* types
                if f.content:
                    kb_content.append(f"--- File: {f.filename} ---\n{f.content}")
            
            return "\n\n".join(kb_content)
        except Exception as e:
            logger.error(f"Failed to fetch knowledge base: {e}")
            return ""

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
        
        # 1. Fetch Knowledge Base (if DB enabled)
        knowledge_context = ""
        if db and bot_id:
            knowledge_context = self._fetch_knowledge_base(db, bot_id)
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
