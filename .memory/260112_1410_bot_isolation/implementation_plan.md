# Implementation Plan - Bot Ownership Isolation

## Goal
Ensure each user can only see and manage their own bots.

## Proposed Changes

### 1. Backend (`session-api`)
- **Dependency**: Create `get_current_user` in `main.py`.
    - It will read `X-User-Email` header.
    - Validate that the email exists in `AdminUser` table (optional but good practice).
    - Return the `AdminUser` object.
- **`list_bots` Endpoint**:
    - Add `current_user: AdminUser = Depends(get_current_user)`.
    - Filter query: `db.query(Bot).filter(Bot.user_id == current_user.email)` (assuming user_id stores email, or we map it. Existing data uses 'U...' which looks like LINE ID, but dashboard users authenticate via Google. We need to align this. `AdminUser.id` is UUID? `AdminUser` has `email`. `Bot.user_id` should probably store `email` for dashboard-created bots, or `AdminUser.id`).
    - *Decision*: Use `email` as the stable identifier for now given Google Auth.
- **`create_bot` Endpoint**:
    - Assign `new_bot.user_id = current_user.email`.

### 2. Frontend (`admin-dashboard`)
- **API Client**: Update `src/lib/api.ts`.
    - Add an interceptor or helper to inject `X-User-Email`?
    - Or update specific calls.
    - Since `useSession` hook provides email, we can pass it.
    - **Issue**: `api.ts` is outside React components.
    - **Solution**: Pass `email` as an argument to API functions, OR use `axios` interceptor if we can access session.
    - Easier Approach: Update the `fetchBots` function (wherever it is) to accept `userEmail` and pass it in headers.

## Verification
- Create 2 users (if possible) or simulate by changing `X-User-Email` in curl.
- Verify User A sees only A's bots.
- Verify User B sees only B's bots.
