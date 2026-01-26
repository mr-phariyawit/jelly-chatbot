# Jelly ChatBot - AI Support Platform

AI-powered multi-tenant chatbot platform for LINE Official Accounts with Knowledge Base (RAG), Admin Dashboard, and JIRA integration.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  LINE Official  │────▶│   Session API    │────▶│   PostgreSQL    │
│    Accounts     │     │   (Cloud Run)    │     │ + pgvector      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Admin Dashboard │
                        │   (Cloud Run)    │
                        └──────────────────┘
```

## Features

- **Multi-tenant Bots** - Manage multiple LINE OA bots from single platform
- **Trigger Names** - Configure custom names for bots to respond in group chats (e.g., "@bot", "bot")
- **AI Chat** - Gemini 2.0 Flash for natural language understanding
- **Knowledge Base (RAG)** - Vector search with pgvector embeddings
- **File Upload** - PDF, TXT, XLSX support with GCS storage
- **Admin Dashboard** - Next.js 15 with Google OAuth
- **Session Management** - Track and analyze chat sessions
- **Auto-Escalation** - Automatic JIRA ticket creation
- **Admin Approval** - Whitelist-based access control

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend API | Python FastAPI |
| Frontend | Next.js 15 (App Router) |
| Database | PostgreSQL + pgvector |
| AI/LLM | Google Gemini 2.0 Flash |
| Storage | Google Cloud Storage |
| Auth | NextAuth.js + Google OAuth |
| Hosting | Google Cloud Run |

## Production URLs

- **API**: https://session-api-687023036300.us-central1.run.app
- **Dashboard**: https://admin-dashboard-687023036300.us-central1.run.app

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL with pgvector extension
- Google Cloud SDK
- LINE Developer Account

### Local Development

1. **Clone & Setup API**
   ```bash
   cd api
   cp .env.example .env
   # Edit .env with your credentials
   pip install -r requirements.txt
   python3 -m uvicorn main:app --reload --port 8001
   ```

2. **Setup Admin Dashboard**
   ```bash
   cd admin-dashboard
   cp .env.example .env.local
   # Edit .env.local with your credentials
   npm install
   npm run dev
   ```

3. **Configure Google OAuth**
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `http://localhost:3000/api/auth/callback/google`

### Environment Variables

#### API (.env)
```bash
GEMINI_API_KEY=your_gemini_api_key
GCS_BUCKET_NAME=your_bucket_name
SUPER_ADMIN_EMAILS=admin@example.com
```

#### Dashboard (.env.local)
```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_secret
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## Project Structure

```
.
├── api/                      # Python FastAPI Backend
│   ├── app/
│   │   └── routers/          # API endpoints
│   │       ├── auth.py       # Authentication
│   │       ├── bots.py       # Bot management
│   │       ├── files.py      # File upload/indexing
│   │       ├── sessions.py   # Chat sessions
│   │       └── webhooks.py   # LINE webhook handler
│   ├── models.py             # SQLAlchemy models
│   ├── processor.py          # AI message processor
│   └── ingestion_service.py  # RAG indexing
│
├── admin-dashboard/          # Next.js Frontend
│   └── src/
│       ├── app/              # App Router pages
│       │   ├── admin/        # Admin pages
│       │   │   ├── bots/     # Bot management
│       │   │   ├── sessions/ # Session viewer
│       │   │   └── settings/ # User settings
│       │   └── login/        # Login page
│       ├── components/       # React components
│       └── lib/              # Utilities
│
└── docs/                     # Documentation
```

## Deployment

### Deploy API
```bash
cd api
gcloud builds submit --tag gcr.io/PROJECT_ID/session-api
gcloud run deploy session-api \
  --image gcr.io/PROJECT_ID/session-api \
  --region us-central1 \
  --allow-unauthenticated
```

### Deploy Dashboard
```bash
cd admin-dashboard
gcloud builds submit --config cloudbuild.yaml
gcloud run deploy admin-dashboard \
  --image gcr.io/PROJECT_ID/admin-dashboard \
  --region us-central1 \
  --allow-unauthenticated
```

## LINE Bot Setup

1. Create bot in Admin Dashboard
2. Copy the Webhook URL from bot settings
3. Go to [LINE Developers Console](https://developers.line.biz/)
4. Paste Webhook URL and enable webhook
5. Upload knowledge base files to the bot

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/bots` | List all bots |
| POST | `/bots` | Create new bot |
| GET | `/bots/{id}` | Get bot details |
| POST | `/bots/{id}/files/signed-url` | Get upload URL |
| GET | `/sessions` | List chat sessions |
| POST | `/webhook/{bot_id}` | LINE webhook |

## License

Private - Jelly ChatBot Platform
