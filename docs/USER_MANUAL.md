# AI Support Assistant - Admin Dashboard User Manual

This manual provides a guide for administrators to manage LINE bots, knowledge base files, and chat sessions using the AI Support Assistant Admin Dashboard.

## Accessing the Dashboard
- **URL**: `https://admin-dashboard-687023036300.us-central1.run.app`
- **Login**: (Currently open access / restricted via internal network as per configuration)

## 1. Dashboard Overview
The dashboard provides a real-time view of your AI support ecosystem.
- **Active Bots**: Total number of bots configured.
- **Active Sessions**: Number of ongoing chat sessions.
- **Total Messages**: Aggregate message count across all bots.
- **Recent Activity**: A list of the latest chat interactions awaiting review.

## 2. Managing Bots
To add a new LINE bot to the platform:
1.  Navigate to the **Bots** section in the sidebar.
2.  Click the **"Add New Bot"** button.
3.  Fill in the required details:
    *   **Bot Name**: A friendly name for internal reference.
    *   **Channel ID**: Found in LINE Developers Console (Messaging API settings).
    *   **Channel Secret**: Found in LINE Developers Console (Basic Settings).
    *   **Channel Access Token**: Found in LINE Developers Console (Messaging API settings).
4.  Click **Save**.
5.  **Important**: Copy the generated **Webhook URL** (e.g., `.../webhook/a1b2c3d4`) and paste it into the **Webhook settings** of your bot in the LINE Developers Console. Verify and enable webhooks there.

## 3. Knowledge Base Management
You can upload documents that the AI will use to answer user questions.
1.  Select a specific Bot from the list.
2.  Go to the **"Files"** tab.
3.  Click **"Upload File"**.
4.  Select your file (PDF, TXT, CSV accepted).
5.  The file will ideally be processed and used for context in future chats (RAG implementation pending Phase 2).

## 4. Monitoring Chat Sessions
1.  Navigate to **Sessions**.
2.  You will see a list of chat sessions grouped by User and Bot.
3.  **Status**:
    *   `Active`: Ongoing conversation.
    *   `Closed`: Session timed out (30 mins inactivity).
    *   `Escalated`: The user requested human support (future feature).
4.  Click on a session ID to view the full **Chat Transcript**.

## Troubleshooting
- **Bot not replying?**
    - Check if "Use Webhook" is enabled in LINE Developers Console.
    - Check if the Webhook URL matches the one in the dashboard.
    - Ensure "Auto-reply" is disabled in LINE Official Account Manager.
- **Changes not saving?**
    - Verify your internet connection.
    - Check if the API service is running (Green status indicator).

## Support
For technical issues, contact the AI-KMS Platform Team.
