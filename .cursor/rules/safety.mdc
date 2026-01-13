---
description: Critical safety protocols and forbidden actions
globs: "**/*"
---
# Safety Rules (Article I)

## 1. Destructive Actions
- **Rule:** You are FORBIDDEN from deleting code or files without explicit user approval or a backup plan.
- **Commands:** NEVER use `rm -rf`, `format`, or `fdisk`.

## 2. Authentication & Secrets
- **Rule:** NEVER commit secrets (API keys, passwords) to git.
- **Enforcement:** Always use `.env` files and verify `.gitignore`.

## 3. Deployment Safety
- **Rule:** NEVER deploy to production without passing tests.
- **Protocol:** Run `deploy.sh` (which runs tests) instead of raw `gcloud/firebase` commands when possible.
