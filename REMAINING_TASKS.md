# Remaining Tasks - Jelly ChatBot Project

Generated: 2026-01-22

## Current Status Summary

✅ **Completed:**

- Jelly ChatBot rebrand implementation (frontend + backend)
- Logo generation and asset creation
- Color scheme update (Pink & Lavender)
- Production deployment of rebrand changes
- Both dev servers running locally (frontend:3000, backend:8001)

⚠️ **Pending Tasks Below**

---

## 1. Backend Feature: Commit & Deploy Trigger Names

**Priority:** Medium

- [x] Fix Frontend OAuth Connection Errors (Minor)

### Description

There are uncommitted changes that add a `trigger_names` feature for LINE bots to respond to specific mentions in group chats (e.g., "@papa", "papa").

### Files Changed

```
M api/app/migrations.py       (+13 lines)
M api/app/routers/bots.py     (+7 lines)
M api/app/routers/webhooks.py (+75 lines)
M api/models.py               (+3 lines)
M api/schemas.py              (+3 lines)
?? api/check_bot_logs.py
?? api/migrate_trigger_names.py
```

### Tasks

### Tasks

- [x] Review the trigger_names implementation in all changed files
- [x] Test the new trigger_names functionality locally
- [x] Commit changes with descriptive message
- [x] Push to GitHub
- [x] Deploy backend to Cloud Run (`gcloud builds submit --tag ... && gcloud run deploy ...`)
- [x] Verify trigger_names field works in production API
- [x] Update frontend to support trigger_names UI (if needed)

### Commands

```bash
# Review changes
git diff api/

# Test locally
curl -X POST http://localhost:8001/bots \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Bot","trigger_names":["@test","test"]}'

# Commit & Push
git add api/
git commit -m "feat: add trigger_names support for LINE group chat mentions"
git push origin main

# Deploy
cd api
gcloud config set project ai-kms-platform
gcloud builds submit --tag gcr.io/ai-kms-platform/session-api
gcloud run deploy session-api \
  --image gcr.io/ai-kms-platform/session-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 2. Fix SQLite Migration Compatibility

**Priority:** Low (doesn't break functionality)
**Estimated Effort:** 20 minutes

### Description

Migration scripts in `api/app/migrations.py` use PostgreSQL's `information_schema.columns` which doesn't exist in SQLite. This causes errors on local development but doesn't break the server.

### Current Errors

```
Migration error (is_approved): no such table: information_schema.columns
Migration error (indexing_progress): no such table: information_schema.columns
Migration error (trigger_names): no such table: information_schema.columns
```

### Tasks

### Tasks

- [x] Read [api/app/migrations.py](api/app/migrations.py)
- [x] Replace `information_schema.columns` queries with SQLite-compatible version using `PRAGMA table_info()`
- [x] Test migrations on both SQLite (local) and PostgreSQL (production)
- [x] Commit fix

### Solution Approach

```python
# Current (PostgreSQL only):
result = db.execute(text("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name='bots' AND column_name='trigger_names';
"""))

# Fix (SQLite compatible):
import sqlite3
from sqlalchemy import inspect

# Use SQLAlchemy inspector instead
inspector = inspect(db.bind)
columns = [col['name'] for col in inspector.get_columns('bots')]
column_exists = 'trigger_names' in columns
```

---

## 3. Asset Cleanup & Gitignore

**Priority:** Low
**Estimated Effort:** 5 minutes

### Description

Temporary logo generation files in `assets/` folder should be organized or gitignored.

### Untracked Files

```
?? assets/apple-touch-icon.png
?? assets/favicon-32.png
?? assets/jelly-square.png
?? assets/jelly.png
?? assets/logo.png
?? assets/profile-jelly.png
?? assets/text-icon.png
```

### Tasks

### Tasks

- [x] Keep `assets/jelly.png` as the source logo file
- [x] Delete intermediate files (`jelly-square.png`, `favicon-32.png`)
- [x] Add `assets/*.png` to `.gitignore` (except jelly.png)
- [x] Or: Organize into `assets/generated/` folder

### Commands

```bash
# Option 1: Keep only source
cd /Users/mr.phariyawit/Documents/ai-support
git add assets/jelly.png
echo "assets/*.png\n!assets/jelly.png" >> .gitignore
rm assets/jelly-square.png assets/favicon-32.png

# Option 2: Organize
mkdir -p assets/generated
mv assets/{apple-touch-icon,favicon-32,jelly-square,logo,profile-jelly,text-icon}.png assets/generated/
echo "assets/generated/" >> .gitignore
```

---

## 4. Manual Asset Creation (Optional)

**Priority:** Low (optional improvements)
**Estimated Effort:** 15 minutes

### Description

Create vector and ICO versions of the logo for better quality across platforms.

### Missing Assets

- `favicon.ico` - Multi-size ICO file for browser compatibility
- `logo.svg` - Vector version for scalability
- `favicon.svg` - Vector favicon for modern browsers

### Tasks

- [ ] Convert `favicon-32.png` to `favicon.ico` using <https://www.icoconverter.com/>
- [ ] Trace `jelly-square.png` to SVG using <https://www.autotracer.org/> or Inkscape
- [ ] Save as `logo.svg` and `favicon.svg`
- [ ] Copy to `admin-dashboard/public/`
- [ ] Update `admin-dashboard/src/app/layout.tsx` to reference `.svg` icons

### Commands

```bash
# After manual creation:
cp logo.svg favicon.svg admin-dashboard/public/
```

---

## 5. Fix Frontend OAuth Connection Errors (Minor)

**Priority:** Low (cosmetic issue)
**Estimated Effort:** None (already fixed, just needs testing)

### Description

Frontend logs show `ECONNREFUSED` errors during Google OAuth flow. This was from before the backend was started. These errors should stop appearing on the next login attempt.

### Error Context

```
[stderr] Failed to sync user with backend: TypeError: fetch failed
    at async signIn (src/lib/auth.ts:21:11)
  code: 'ECONNREFUSED'
```

### Tasks

### Tasks

- [x] Test Google OAuth login at <http://localhost:3000/login>
- [x] Verify no ECONNREFUSED errors in console
- [x] Confirm user sync with backend works (check backend logs for `/auth/google` POST request)

### Expected Result

```
# Backend log should show:
INFO: POST /auth/google HTTP/1.1 200 OK
INFO: GET /auth/me?email=user@example.com HTTP/1.1 200 OK

# Frontend should successfully redirect to /admin/bots
```

---

## 6. Frontend: Add Trigger Names UI (Future Enhancement)

**Priority:** Medium (depends on backend deployment)
**Estimated Effort:** 45 minutes

### Description

Once `trigger_names` backend feature is deployed, add UI in admin dashboard for managing bot trigger names.

### Tasks

### Tasks

- [x] Add "Trigger Names" field to bot creation form ([admin-dashboard/src/app/admin/bots/create/page.tsx](admin-dashboard/src/app/admin/bots/create/page.tsx))
- [x] Add "Trigger Names" field to bot edit form ([admin-dashboard/src/app/admin/bots/[id]/edit/page.tsx](admin-dashboard/src/app/admin/bots/[id]/edit/page.tsx))
- [x] Display trigger names in bot list view
- [x] Add validation: array of strings, max 5 items, no duplicates
- [x] Add UI hints: "Names that trigger bot in group chats (e.g., @papa, papa)"

### UI Mock

```tsx
<div>
  <Label>Trigger Names (Optional)</Label>
  <p className="text-sm text-muted-foreground">
    Names that will trigger this bot in LINE group chats
  </p>
  <Input
    placeholder="@papa, papa, พ่อปาป้า"
    value={triggerNames.join(', ')}
    onChange={(e) => setTriggerNames(e.target.value.split(',').map(s => s.trim()))}
  />
</div>
```

---

## 7. Documentation Updates (Optional)

**Priority:** Low
**Estimated Effort:** 10 minutes

### Tasks

### Tasks

- [x] Update [docs/README.md](docs/README.md) with trigger_names feature documentation
- [ ] Add API endpoint examples for `/bots` with trigger_names
- [ ] Document LINE group chat trigger behavior
- [ ] Update architecture diagram if needed

---

## Summary Checklist

**High Priority:**

- [ ] Commit & deploy backend trigger_names feature (Task 1)
- [ ] Test OAuth login flow (Task 5)

**Medium Priority:**

- [ ] Add trigger_names UI in frontend (Task 6)

**Low Priority:**

- [ ] Fix SQLite migration compatibility (Task 2)
- [ ] Clean up asset files (Task 3)
- [ ] Create manual vector assets (Task 4)
- [ ] Update documentation (Task 7)

---

## Notes for Gemini Code

### Current System State

- **Frontend Dev Server:** <http://localhost:3000> (Running in background - Task ID: bc95791)
- **Backend API Server:** <http://localhost:8001> (Running in background - Task ID: b976f92)
- **Git Branch:** main
- **GCP Project:** ai-kms-platform
- **Production URLs:**
  - Frontend: <https://admin-dashboard-1088865818405.us-central1.run.app> (Project: jelly-chatbot-platform)
  - Backend: <https://session-api-687023036300.us-central1.run.app> (Project: ai-kms-platform)

### Environment

- Working Directory: `/Users/mr.phariyawit/Documents/ai-support`
- Python Version: 3.9.6 (consider upgrading to 3.10+ per warnings)
- Node.js: Next.js 16.1.1 with Turbopack

### Important Context

1. The rebrand from "PaPa ChatBot" to "Jelly ChatBot" is complete and deployed
2. New color scheme: Pink (#FF8FAB) & Lavender (#C8B3E0)
3. All logo files use `profile-jelly.png` (600x600)
4. Backend uses SQLite locally, PostgreSQL in production
5. Frontend auth uses NextAuth.js with Google OAuth

### Useful Commands

```bash
# Check server status
lsof -ti:3000  # Frontend
lsof -ti:8001  # Backend

# View server logs
tail -f /private/tmp/claude/-Users-mr-phariyawit-Documents-ai-support/tasks/bc95791.output  # Frontend
tail -f /private/tmp/claude/-Users-mr-phariyawit-Documents-ai-support/tasks/b976f92.output  # Backend

# Restart servers if needed
pkill -f "next dev"
pkill -f "uvicorn"
cd admin-dashboard && npm run dev &
cd api && python3 -m uvicorn main:app --reload --port 8001 &
```

---

**End of Document**
