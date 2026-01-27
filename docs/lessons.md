# Lessons Learned

## 2026-01-27: Auth API URL Fallback Bug

### Problem

User stuck on "Pending Approval" page even after being approved and re-logging in.

### Root Cause

`admin-dashboard/src/lib/auth.ts` had hardcoded fallback URL pointing to OLD project (`687023036300`) instead of NEW project (`1088865818405`).

`NEXT_PUBLIC_*` env vars are embedded at **build time**, not runtime. Docker build didn't have the env var, so code fell back to wrong URL.

### Solution

Updated hardcoded fallback URLs in `auth.ts` lines 20 & 46:

```typescript
// ✅ Correct
const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://session-api-1088865818405.us-central1.run.app";
```

### Prevention

- Always update hardcoded fallback URLs when migrating projects
- Search codebase for old project IDs after migration
- Consider using server-side env vars (non-NEXT_PUBLIC_) for server code

---
