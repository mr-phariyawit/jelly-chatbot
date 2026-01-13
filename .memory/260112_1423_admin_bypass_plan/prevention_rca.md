# Root Cause Analysis (RCA) - "Why did this happen?"

## The Issue
We encountered two critical regressions in production:
1. **Stale Code (404 Error)**: `session-api` was deployed without the latest changes (missing endpoints).
2. **Crash Loop (500 Error)**: `AttributeError` calling `bot.model_config_json` (which didn't exist) instead of `bot.model_config`.

## Why Preventions Failed
The user correctly noted we "understood preventions were in place." However, our current setup relied on **Philosophy (SDD)** but lacked **Enforcement (CI/CD)**.

### 1. Human Error vs. Machine Check
- **The Mistake**: A field was renamed in `models.py` (`model_config_json` -> `model_config`) but a reference in `main.py` was missed.
- **Why it slipped**: 
    - Python is a dynamic language; it doesn't fail at compile time.
    - We have *no static analysis* (like `mypy`) configured in the project to catch this basic type error.
    - We have *no automated unit tests* running before deployment.

### 2. The Deployment Gap
- We used `gcloud builds submit` and `gcloud run deploy` directly.
- **Missing Gate**: There is no `pre-deploy` script that runs tests. If there were, the build would have failed immediately upon hitting the broken code.

## Proposed Prevention (The "Real" Fix)
To prevent this *permanently*, we must move from "Agent Promises" to "System Constraints":

1.  **Add `pytest` & `mypy`**: Install standard testing and type-checking tools.
2.  **Create a `deploy.sh` script**: 
    - STEP 1: Run Tests (`pytest`) -> STOP if fail.
    - STEP 2: Run Type Check (`mypy`) -> STOP if fail.
    - STEP 3: Deploy to Cloud Run.
3.  **Strict Rule**: NEVER run `gcloud run deploy` manually. Always use the script.
