# Feature: Account Approval System

## Goal
Implement a system where new users must be approved by an admin before accessing the dashboard.
- [x] **Pending Approval Page**: Beautiful waiting UI for unapproved users.
- [x] **Auth Enforcement**: Redirect unapproved users automatically.
- [x] **Admin Control**: Toggle approval status in settings.
- [x] **Super Admin Whitelist**: Automatic approval and promotion for whitelisted emails.

## User Review Required

> [!IMPORTANT]
> This change updates the `AdminUser` table. New users will default to `is_approved: false`.
> Existing users were automatically approved during migration.
> Whitelisted emails in `SUPER_ADMIN_EMAILS` are automatically approved and assigned `super-admin` role.

---

## Proposed Changes

### Backend (`api`)

#### [MODIFY] [models.py](file:///Users/mr.phariyawit/Documents/ai-support/api/models.py)
- Update `AdminUser` model:
  - Add `is_approved = Column(Boolean, default=False)`
  - Update `to_dict` to include `is_approved`

#### [MODIFY] [schemas.py](file:///Users/mr.phariyawit/Documents/ai-support/api/schemas.py)
- Update `AdminUserResponse` to include `is_approved: bool`

#### [MODIFY] [auth.py](file:///Users/mr.phariyawit/Documents/ai-support/api/app/routers/auth.py)
- Update local `AdminUserResponse` and `AdminUserUpdate` schemas
- Update `google_auth` to handle `is_approved` (default false for new users)
- Update `update_user` to allow toggling `is_approved`
- [NEW] Super Admin logic in `google_auth`: Check `SUPER_ADMIN_EMAILS` whitelist

---

### Frontend (`admin-dashboard`)

#### [MODIFY] [api.ts](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/lib/api.ts)
- Update `AdminUser` interface to include `is_approved`

#### [MODIFY] [auth.ts](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/lib/auth.ts)
- Fetch approval status from backend in `jwt` or `session` callback
- Update `session` type to include `is_approved`

#### [MODIFY] [middleware.ts](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/middleware.ts)
- Add check for `req.auth?.user?.is_approved`
- Redirect to `/pending-approval` if not approved (and not already on that page)

#### [NEW] [page.tsx](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/app/pending-approval/page.tsx)
- Premium dark-themed waiting page matching the mockup

#### [MODIFY] [page.tsx](file:///Users/mr.phariyawit/Documents/ai-support/admin-dashboard/src/app/admin/settings/page.tsx)
- Add **User Management** section
- List users with a toggle switch for `is_approved`
- [MODIFY] **User Management UI**: Added `super-admin` role badges and disabled toggles for whitelisted accounts

---

## UI Mockup

![Pending Approval Mockup](/Users/mr.phariyawit/.gemini/antigravity/brain/2be99ee5-6208-410e-8d57-e2022c90526e/pending_approval_page_1768570624822.png)

---

## Verification Plan

### Automated Tests
- [ ] Backend: Test `is_approved` field in auth endpoints
- [ ] Frontend: Test redirection in middleware

### Manual Verification
1. Log in with a new Google Account
2. Verify redirection to `/pending-approval`
3. Log in with Admin account
4. Go to Settings -> User Management
5. Toggle "Approve" for the new user
6. Refresh the new user's browser, verify dashboard access
