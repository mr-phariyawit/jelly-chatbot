/**
 * IT Support Message Processor
 * 
 * Main logic for processing support requests using AI (Gemini)
 */

import { GoogleGenAI } from '@google/genai';
import { defineSecret } from 'firebase-functions/params';
import { getFirestore } from 'firebase-admin/firestore';
import { initializeApp, getApps } from 'firebase-admin/app';
import { logUserMessage, logAssistantMessage } from '../utils/session';

// Initialize Firebase if not already initialized
if (getApps().length === 0) {
    initializeApp();
}

const db = getFirestore();

// Define Gemini API Key secret
const geminiApiKey = defineSecret('GEMINI_API_KEY');

// Get Generative Model
function getAI() {
    return new GoogleGenAI({ apiKey: geminiApiKey.value() });
}

// System prompt for IT Support Assistant
const SYSTEM_PROMPT = `คุณคือ AI Support Assistant ของ JVC (J Ventures) ทำหน้าที่ช่วยเหลือพนักงานหน้าร้านแก้ไขปัญหาเกี่ยวกับแอปพลิเคชันต่างๆ

⚠️ กฎสำคัญในการตอบ:
• ห้ามใช้ markdown เช่น **, ##, - bullet ให้ใช้ข้อความธรรมดา
• ใช้ emoji ได้แต่ต้องสุภาพและ professional เช่น ✅ ❌ 📱 💡 🔧
• ใช้ขึ้นบรรทัดใหม่แทนการใช้ bullet points
• ตอบสั้นกระชับ เข้าใจง่าย

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

เมื่อต้องส่งต่อ ให้ขึ้นต้นข้อความด้วย [ESCALATE] ตามด้วยสรุปปัญหาสั้นๆ และแจ้งผู้ใช้ว่าได้ส่งเรื่องให้เจ้าหน้าที่แล้ว`;

interface MessageInput {
    userId: string;
    messageType: 'text' | 'image';
    content: string;
    imageUrl?: string;
}

interface MessageOutput {
    message: string;
    shouldEscalate: boolean;
    incidentId?: string;
    jiraTicketKey?: string;
}

/**
 * Process IT support message with AI
 */
export async function processITSupportMessage(
    input: MessageInput
): Promise<MessageOutput> {
    try {
        // Get conversation history
        const conversationRef = db.collection('support_conversations').doc(input.userId);
        const conversationDoc = await conversationRef.get();

        let messages: Array<{ role: string; content: string }> = [];

        if (conversationDoc.exists) {
            messages = conversationDoc.data()?.messages || [];
        }

        // Add user message to history
        messages.push({
            role: 'user',
            content: input.content,
        });

        // Generate AI response using new @google/genai API
        const ai = getAI();

        // Build the conversation context
        const conversationContext = messages.map(m =>
            `${m.role === 'user' ? 'ผู้ใช้' : 'AI'}: ${m.content}`
        ).join('\n');

        const prompt = `${SYSTEM_PROMPT}

บทสนทนาที่ผ่านมา:
${conversationContext}

คำถามล่าสุด: ${input.content}

กรุณาตอบในฐานะ AI Support Assistant:`;

        const result = await ai.models.generateContent({
            model: 'gemini-2.5-flash',
            contents: prompt,
        });

        // Strip markdown from response (LINE doesn't support it)
        let aiResponse = result.text ||
            'ขออภัยค่ะ ไม่สามารถประมวลผลได้ กรุณาลองใหม่อีกครั้ง';

        // Remove markdown formatting
        aiResponse = aiResponse
            .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove **bold**
            .replace(/\*([^*]+)\*/g, '$1')      // Remove *italic*
            .replace(/#{1,6}\s/g, '')           // Remove # headers
            .replace(/^[-*]\s/gm, '• ')         // Convert - or * bullet to •
            .replace(/```[\s\S]*?```/g, '')     // Remove code blocks
            .replace(/`([^`]+)`/g, '$1')        // Remove inline code
            .trim();

        // Check if AI wants to escalate - primary check for [ESCALATE] keyword
        console.log('AI Response preview:', aiResponse.substring(0, 200));
        let shouldEscalate = aiResponse.includes('[ESCALATE]');

        // Fallback: detect Thai escalation phrases if AI forgot to use [ESCALATE]
        if (!shouldEscalate) {
            const thaiEscalatePatterns = [
                'ส่งต่อปัญหานี้ให้เจ้าหน้าที่',
                'ส่งต่อให้เจ้าหน้าที่',
                'โปรดรอการติดต่อจากเจ้าหน้าที่',
                'เจ้าหน้าที่จะติดต่อกลับ',
            ];
            shouldEscalate = thaiEscalatePatterns.some(pattern => aiResponse.includes(pattern));
            if (shouldEscalate) {
                console.log('Escalation detected via Thai fallback patterns');
            }
        }

        console.log('Should escalate:', shouldEscalate);
        let finalMessage = aiResponse.replace('[ESCALATE]', '').trim();

        // Log user message to Session API
        const userLogResult = await logUserMessage(input.userId, input.content);
        console.log('User message logged:', userLogResult?.session_id, 'is_new:', userLogResult?.is_new_session);

        if (shouldEscalate) {
            console.log('Escalation triggered, logging to session...');
            // Log assistant response with escalation flag
            const assistantLogResult = await logAssistantMessage(
                input.userId,
                finalMessage,
                true,
                input.content.substring(0, 100)
            );
            console.log('Escalated session:', assistantLogResult?.session_id);
            finalMessage += `\n\nSession ${assistantLogResult?.session_id?.substring(0, 8)} บันทึกเรียบร้อย ส่งต่อให้เจ้าหน้าที่แล้วค่ะ 📋`;
        } else {
            // Log normal assistant response
            await logAssistantMessage(input.userId, finalMessage, false);
        }

        // Add AI response to history
        messages.push({
            role: 'assistant',
            content: aiResponse,
        });

        // Save conversation
        await conversationRef.set({
            userId: input.userId,
            messages,
            updatedAt: new Date(),
        }, { merge: true });

        return {
            message: finalMessage,
            shouldEscalate,
        };
    } catch (error) {
        console.error('Error processing message:', error);
        throw error;
    }
}

// Export for Cloud Function
export { processITSupportMessage as processMessage };
