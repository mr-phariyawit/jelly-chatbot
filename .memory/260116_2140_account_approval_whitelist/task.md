# Account Approval Feature

- [x] Backend Implementation <!-- id: 0 -->
    - [x] Add `is_approved` to User model & schemas <!-- id: 1 -->
    - [x] Update auth endpoints logic <!-- id: 2 -->
- [x] Frontend: Session & Guard <!-- id: 3 -->
    - [x] Update `AdminUser` API interface <!-- id: 4 -->
    - [x] Sync `is_approved` in NextAuth session <!-- id: 5 -->
    - [x] Implement middleware redirection <!-- id: 6 -->
- [x] Frontend: UI Components <!-- id: 7 -->
    - [x] Create `/pending-approval` page <!-- id: 8 -->
    - [x] Create User Management section in Settings <!-- id: 9 -->
- [x] Verification <!-- id: 10 -->
    - [x] Test end-to-end flow <!-- id: 11 -->
- [x] Super Admin Whitelist <!-- id: 12 -->
    - [x] Backend: Add `SUPER_ADMIN_EMAILS` to `.env` <!-- id: 13 -->
    - [x] Backend: Update `config.py` and `auth.py` logic <!-- id: 14 -->
    - [x] Frontend: Add support for `super-admin` role in Settings <!-- id: 15 -->
    - [x] Verification: Deploy and test whitelist <!-- id: 16 -->
