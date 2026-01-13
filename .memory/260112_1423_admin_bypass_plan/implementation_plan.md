# Implementation Plan - Bot Ownership Isolation & Migration

## Goal
Ensure each user can only see and manage their own bots, while restoring access to legacy bots for the admin.

## Implemented Changes
### 1. Backend (`session-api`)
- [x] **Dependency**: Added `get_current_user` logic via `X-User-Email` header.
- [x] **Endpoints**: Updated `list_bots` and `create_bot` to respect ownership.

### 2. Frontend (`admin-dashboard`)
- [x] **API Client**: Updated `BotsPage` and `CreateBotDialog` to send `X-User-Email`.

## Recent Issues
- **Missing Bots**: Legacy bots (created before auth) have `user_id` in LINE format (e.g., "U..."). The new filter `user_id == 'mr.phariyawit@gmail.com'` hides them.

## Proposed Fix: Admin Bypass
### 1. Backend (`session-api`)
- **`list_bots` Logic**:
    - If `X-User-Email` is `mr.phariyawit@gmail.com`, **skip the ownership filter**.
    - This effectively makes this user a "Super Admin" who can see all bots.
    - *Future*: Create a proper migration script to update `user_id` in DB.

- **DB Migration (Optional/Future)**:
    - Update schema to allow `update_bot` to claim ownership.

## Verification
- Deploy Backend.
- User `mr.phariyawit@gmail.com` logs in and should see all bots.
