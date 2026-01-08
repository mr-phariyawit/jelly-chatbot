# AI Support Assistant - Technical Walkthrough

## สถานะปัจจุบัน ✅

LINE Bot ทำงานได้สมบูรณ์แล้ว!
- Signature validation ผ่าน
- AI (Gemini 2.5 Flash) ตอบกลับได้
- Markdown stripping สำหรับ LINE

---

## Tech Stack Overview

```mermaid
flowchart TB
    subgraph "User Interface"
        LINE[LINE Official Account<br/>PaPa]
    end
    
    subgraph "LINE Platform"
        WEBHOOK[LINE Messaging API<br/>Webhook Events]
    end
    
    subgraph "Google Cloud Platform"
        CF[Cloud Functions<br/>lineWebhook]
        SM[Secret Manager<br/>API Keys & Tokens]
        GEMINI[Gemini 2.5 Flash<br/>AI Processing]
        FS[Firestore<br/>Conversation History]
    end
    
    subgraph "External Services"
        JIRA[Jira Cloud<br/>Ticket Escalation]
    end
    
    LINE -->|Send Message| WEBHOOK
    WEBHOOK -->|POST /lineWebhook| CF
    CF -->|Get Secrets| SM
    CF -->|Generate Response| GEMINI
    CF -->|Store/Retrieve History| FS
    CF -->|Create Ticket| JIRA
    CF -->|Reply| LINE
```

---

## Sequence Diagram - Message Flow

```mermaid
sequenceDiagram
    participant U as พนักงานหน้าร้าน
    participant L as LINE OA (PaPa)
    participant W as Cloud Function<br/>(lineWebhook)
    participant S as Secret Manager
    participant G as Gemini AI
    participant F as Firestore
    participant J as Jira

    U->>L: ส่งข้อความ "ไม่ได้รับ OTP"
    L->>W: POST webhook + x-line-signature
    
    Note over W: Validate Signature
    W->>S: Get LINE_CHANNEL_SECRET
    S-->>W: Secret value
    W->>W: Verify HMAC-SHA256
    
    Note over W: Load Conversation
    W->>F: Get conversation history
    F-->>W: Previous messages
    
    Note over W: AI Processing
    W->>S: Get GEMINI_API_KEY
    S-->>W: API Key
    W->>G: generateContent(prompt)
    G-->>W: AI Response
    
    Note over W: Post-processing
    W->>W: Strip markdown (**,#,etc)
    W->>W: Check [ESCALATE]
    
    alt Needs Escalation
        W->>J: Create ticket
        J-->>W: Ticket key (CS-123)
    end
    
    W->>F: Save conversation
    W->>L: Reply message
    L->>U: แสดงคำตอบจาก AI
```

---

## กระบวนการทำงานโดยละเอียด

### 1. รับข้อความ (Webhook)
- LINE ส่ง POST request ไปที่ `lineWebhook` Cloud Function
- Header `x-line-signature` ใช้ verify ว่ามาจาก LINE จริง

### 2. ตรวจสอบความถูกต้อง (Signature Validation)
- ใช้ `rawBody` + `LINE_CHANNEL_SECRET`
- คำนวณ HMAC-SHA256 เปรียบเทียบกับ signature
- ปฏิเสธ request ที่ไม่ถูกต้อง

### 3. โหลดประวัติสนทนา
- ดึงข้อมูลจาก Firestore collection `support_conversations`
- ใช้ `userId` เป็น document ID

### 4. ประมวลผล AI
- สร้าง prompt รวม System Prompt + ประวัติ + คำถาม
- เรียก Gemini 2.5 Flash ผ่าน `@google/genai`
- ลบ markdown formatting (**, #, backticks)

### 5. ตรวจสอบ Escalation
- ถ้า AI ตอบ `[ESCALATE]` → สร้าง Jira ticket
- เพิ่มเลข ticket ในข้อความตอบกลับ

### 6. ตอบกลับผู้ใช้
- บันทึกประวัติลง Firestore
- ส่ง reply กลับผ่าน LINE API

---

## 💡 ควรมี Webapp จัดการ Datasource หรือไม่?

### แนะนำ: **ควรมี** สำหรับ Phase 2

### เหตุผล:

| ปัจจุบัน                        | ปัญหา                      |
| ---------------------------- | ------------------------- |
| Knowledge อยู่ใน System Prompt | ต้อง deploy ใหม่ทุกครั้งที่อัพเดท |
| ไม่มี UI จัดการ                 | IT Admin แก้ไขเองไม่ได้      |
| ไม่มี analytics                | ไม่รู้ว่าปัญหาไหนเกิดบ่อย        |

### Webapp ที่แนะนำ:

```mermaid
flowchart LR
    subgraph "Admin Portal"
        KB[Knowledge Base<br/>จัดการปัญหาและวิธีแก้]
        SYS[System Config<br/>ตั้งค่าระบบ]
        DASH[Dashboard<br/>Analytics & Logs]
    end
    
    subgraph "Storage"
        FS2[Firestore<br/>Knowledge Documents]
    end
    
    subgraph "AI Processing"
        CF2[Cloud Function]
        RAG[RAG Search<br/>Vector Similarity]
    end
    
    KB -->|CRUD| FS2
    CF2 -->|Query| RAG
    RAG -->|Search| FS2
```

### Features แนะนำ:

1. **Knowledge Base Management**
   - เพิ่ม/แก้ไข/ลบ ปัญหาที่พบบ่อย
   - Categorize by system (JDID, SGF+, etc.)
   - Version history

2. **Analytics Dashboard**
   - ปัญหาที่ถามบ่อย
   - อัตราการ escalate
   - Response time

3. **Conversation Logs**
   - ดูประวัติการสนทนา
   - Export สำหรับ training

4. **System Settings**
   - เปลี่ยน AI parameters
   - Manage LINE OA settings

---

## สรุป

| Component            | Status                      |
| -------------------- | --------------------------- |
| LINE Webhook         | ✅ Working                   |
| Signature Validation | ✅ Fixed (secret length bug) |
| Gemini AI            | ✅ Working (2.5-flash)       |
| Markdown Stripping   | ✅ Deployed                  |
| Conversation History | ✅ Firestore                 |
| Jira Escalation      | ⚠️ Code ready, needs testing |
| Admin Webapp         | 📋 Recommended for Phase 2   |
