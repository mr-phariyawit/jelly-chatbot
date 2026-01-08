# JVC IT Support Assistant

AI-powered IT Support chatbot for LINE Official Account, integrated with JIRA for ticket escalation.

## Features

- 🤖 **AI Chat** - Gemini 2.0 Flash for natural language understanding
- 📸 **Image Analysis** - Screenshot analysis for error detection
- 🎫 **Auto-Ticket** - Automatic JIRA ticket creation when escalation needed
- 📚 **Knowledge Base** - RAG with historical incident data

## Quick Start

### Prerequisites

- Node.js 20+
- Firebase CLI (`npm install -g firebase-tools`)
- LINE Official Account (Messaging API enabled)
- JIRA API Token

### Setup

1. **Install dependencies**
   ```bash
   cd functions
   npm install
   ```

2. **Configure Firebase**
   ```bash
   firebase login
   firebase use --add  # Select or create project
   ```

3. **Set secrets**
   ```bash
   firebase functions:secrets:set LINE_CHANNEL_SECRET
   firebase functions:secrets:set LINE_CHANNEL_ACCESS_TOKEN
   firebase functions:secrets:set JIRA_API_TOKEN
   firebase functions:secrets:set JIRA_EMAIL
   ```

4. **Deploy**
   ```bash
   firebase deploy
   ```

5. **Configure LINE Webhook**
   - Go to LINE Developers Console
   - Set Webhook URL: `https://{region}-{project}.cloudfunctions.net/lineWebhook`
   - Enable "Use webhook"

## Development

### Local Testing

```bash
# Start Firebase emulators
firebase emulators:start

# In another terminal, use ngrok for LINE webhook
ngrok http 5001
```

### Project Structure

```
.
├── functions/
│   └── src/
│       ├── index.ts              # Function exports
│       ├── line/
│       │   └── webhook.ts        # LINE webhook handler
│       ├── support/
│       │   └── processor.ts      # AI message processor
│       ├── rag/
│       │   ├── embeddings.ts     # Vector embeddings
│       │   └── search.ts         # Similarity search
│       └── utils/
│           └── jira.ts           # JIRA integration
├── firebase.json
├── firestore.rules
└── .specify/                     # Spec-kit documentation
```

## LINE OA Accounts

| Account     | Purpose               |
| ----------- | --------------------- |
| PaPa        | Development & Testing |
| JVC Support | Production            |

## JIRA Integration

- **Project**: Customer Support (CS)
- **URL**: https://jventures.atlassian.net/jira/software/projects/CS

## Documentation

See `.specify/specs/001-ai-support-assistant/` for:
- `spec.md` - Functional requirements
- `plan.md` - Implementation plan
- `tasks.md` - Task breakdown
