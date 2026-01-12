# JVC AI Support Platform - User Manual (V2)

This manual provides a guide for administrators and users of the JVC AI Support Platform.

## 🔗 Quick Links
- **Admin Dashboard**: [https://admin-dashboard-182206907696.us-central1.run.app](https://admin-dashboard-182206907696.us-central1.run.app)
- **API Documentation**: [https://session-api-182206907696.us-central1.run.app/docs](https://session-api-182206907696.us-central1.run.app/docs)

---

## 👥 For Administrators

### 1. Dashboard Overview
The dashboard provides a real-time view of your AI support ecosystem.
- **Active Bots**: Total number of bots configured.
- **Active Sessions**: Number of ongoing chat sessions.
- **Total Messages**: Aggregate message count across all bots.

### 2. Managing Bots
To add a new LINE bot to the platform:
1.  Navigate to the **Bots** section.
2.  Click **"Add New Bot"**.
3.  Fill in the required details (Channel ID, Secret, Token).
4.  **Important**: Copy the generated **Webhook URL** (e.g., `.../webhook/{bot_id}`) and paste it into the **LINE Developers Console**.

### 3. Knowledge Base Management (RAG)
You can upload documents that the AI will use to answer user questions.
1.  Select a Bot from the list.
2.  Go to the **"Files"** tab.
3.  Click **"Upload File"**.
4.  **Supported Formats**:
    *   **PDF**: Standard documents, manuals.
    *   **CSV / Excel**: Structured data (e.g., WiFi codes, phone extensions, incident logs).
    *   **Text**: Plain text notes.
5.  **Processing**: The system automatically extracts text and tables. The content becomes searchable by the AI immediately.

### 4. Monitoring Feedback
1.  Navigate to the **Sessions** or **Feedback** (future UI) section.
2.  You can view which answers received a "👍 Helpful" or "👎 Not Helpful" rating from users.
3.  Use this data to update your Knowledge Base files (e.g., if users dislike an answer, upload a clearer document).

---

## 📱 For End Users (LINE)

### 1. Asking Questions
Simply type your question in the chat. The AI understands natural language (Thai/English).
> *Example: "ขอรหัส WiFi ชั้น 2 หน่อย"*

### 2. Sending Images (New! 📸)
You can send images directly to the bot for analysis.
- **Error Screenshots**: Take a photo of an error message on your screen. The AI will read the error code and suggest a fix.
- **Equipment Photos**: Send a photo of a device to ask how to use it.

### 3. Rating Responses (New! ⭐)
After every AI answer, you will see a **Quick Reply** menu:
- Tap **👍 Helpful** if the answer solved your problem.
- Tap **👎 Not Helpful** if the answer was wrong or confusing.
*Your feedback directly trains the AI to be smarter!*

---

## 🛠 Troubleshooting
- **Bot not replying?**
    - Check if "Use Webhook" is enabled in LINE Developers Console.
    - Ensure "Auto-reply" is disabled in LINE Official Account Manager.
- **Knowledge not found?**
    - Ensure the relevant file is uploaded in the Dashboard.
    - Check if the file contains clear text (scanned PDFs without OCR might not work well).
