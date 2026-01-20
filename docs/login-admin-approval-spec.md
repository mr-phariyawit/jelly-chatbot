# Login & Admin Approval - Reusable Specification Template

> **Version**: 1.0  
> **Last Updated**: 2026-01-18  
> **Source Project**: JVC AI Support Platform

---

## 1. Overview

ระบบ Authentication และ Admin Approval สำหรับ Admin Dashboard ที่ใช้ Google OAuth 2.0 พร้อมระบบอนุมัติผู้ใช้ใหม่

**Tech Stack**:

- Frontend: Next.js + NextAuth.js
- Backend: FastAPI (Python)
- Database: PostgreSQL

---

## 2. User Roles

| Role          | Description                     | Permissions                |
| ------------- | ------------------------------- | -------------------------- |
| `super-admin` | ผู้ดูแลระบบสูงสุด (กำหนดใน ENV) | ทุกอย่าง + อนุมัติ/ลบ User |
| `admin`       | ผู้ดูแลที่ได้รับอนุมัติแล้ว     | จัดการข้อมูลในระบบ         |
| `user`        | ผู้ใช้ทั่วไป (ถ้ามี)            | ดูข้อมูลเฉพาะตัวเอง        |
| `pending`     | ผู้ใช้ใหม่รอการอนุมัติ          | ไม่มี (แสดงหน้า Pending)   |

---

## 3. Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend (Next.js)
    participant Backend API
    participant Google OAuth
    participant Database

    User->>Frontend (Next.js): Click "Sign in with Google"
    Frontend (Next.js)->>Google OAuth: Redirect to Google
    Google OAuth-->>Frontend (Next.js): Return auth code
    Frontend (Next.js)->>Backend API: POST /auth/google {id_token}
    Backend API->>Google OAuth: Verify token
    Google OAuth-->>Backend API: User info (email, name)
    Backend API->>Database: Check if user exists
    alt New User
        Backend API->>Database: Create user (is_approved=false)
        alt Email in SUPER_ADMIN_EMAILS
            Backend API->>Database: Set role=super-admin, is_approved=true
        end
    end
    Database-->>Backend API: User record
    Backend API-->>Frontend (Next.js): {user, role, is_approved, jwt}
    Frontend (Next.js)->>Frontend (Next.js): Store session
    alt is_approved = true
        Frontend (Next.js)->>User: Redirect to /admin
    else is_approved = false
        Frontend (Next.js)->>User: Redirect to /pending-approval
    end
```

---

## 4. Backend API Endpoints

### 4.1 `POST /auth/google`

**Purpose**: Authenticate user with Google ID token

```python
# Request
{ "id_token": "string" }

# Response (Success)
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "picture": "https://..."
  },
  "role": "super-admin" | "admin" | "user",
  "is_approved": true | false,
  "access_token": "jwt_string"
}

# Response (Error)
{ "detail": "Invalid token" }  # 401
```

### 4.2 `GET /users` (Super-Admin only)

```python
# Headers
Authorization: Bearer <jwt_token>

# Response
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "role": "admin",
    "is_approved": false,
    "created_at": "2026-01-18T00:00:00Z"
  }
]
```

### 4.3 `PATCH /users/{id}/approve` (Super-Admin only)

```python
# Response
{
  "message": "User approved successfully",
  "user": { ... }
}
```

### 4.4 `DELETE /users/{id}` (Super-Admin only)

```python
# Response
{ "message": "User deleted successfully" }
```

---

## 5. Database Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    picture TEXT,
    role VARCHAR(50) DEFAULT 'user',
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast email lookup
CREATE INDEX idx_users_email ON users(email);

-- Index for listing pending approvals
CREATE INDEX idx_users_approval ON users(is_approved, created_at);
```

---

## 6. Environment Variables

### Backend (.env)

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Super Admin (comma-separated)
SUPER_ADMIN_EMAILS=mr.phariyawit@gmail.com,admin@company.com

# JWT
JWT_SECRET=your_secure_random_string
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### Frontend (.env.local)

```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret

# Google OAuth (same as backend)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 7. Frontend Routes

| Route               | Component      | Access      | Description      |
| ------------------- | -------------- | ----------- | ---------------- |
| `/login`            | LoginPage      | Public      | หน้า Login       |
| `/pending-approval` | PendingPage    | Unapproved  | หน้ารอการอนุมัติ |
| `/admin`            | Dashboard      | Approved    | หน้าหลัก Admin   |
| `/admin/users`      | UserManagement | Super-Admin | จัดการผู้ใช้     |

---

## 8. Middleware Logic (Next.js)

```typescript
// src/middleware.ts
import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";

const SUPER_ADMIN_EMAILS = process.env.SUPER_ADMIN_EMAILS?.split(",") || [];

export async function middleware(request: NextRequest) {
  const token = await getToken({ req: request });
  const path = request.nextUrl.pathname;

  // Public routes
  if (path === "/login") {
    if (token) {
      return NextResponse.redirect(new URL("/admin", request.url));
    }
    return NextResponse.next();
  }

  // Protected routes
  if (path.startsWith("/admin")) {
    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Check approval status
    const isApproved = token.is_approved as boolean;
    const email = token.email as string;
    const isSuperAdmin = SUPER_ADMIN_EMAILS.includes(email);

    if (!isApproved && !isSuperAdmin) {
      if (path !== "/pending-approval") {
        return NextResponse.redirect(new URL("/pending-approval", request.url));
      }
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/admin/:path*", "/pending-approval"],
};
```

---

## 9. Key Implementation Files

### Backend (FastAPI)

| File                   | Purpose                            |
| ---------------------- | ---------------------------------- |
| `app/routers/auth.py`  | Google OAuth + JWT generation      |
| `app/routers/users.py` | User CRUD + approval               |
| `app/config.py`        | Settings & SUPER_ADMIN_EMAILS      |
| `app/models.py`        | SQLAlchemy User model              |
| `app/dependencies.py`  | Auth dependency (get_current_user) |

### Frontend (Next.js)

| File                                | Purpose                     |
| ----------------------------------- | --------------------------- |
| `src/lib/auth.ts`                   | NextAuth configuration      |
| `src/middleware.ts`                 | Route protection            |
| `src/app/login/page.tsx`            | Login UI with Google button |
| `src/app/pending-approval/page.tsx` | Waiting screen UI           |
| `src/app/admin/users/page.tsx`      | User management table       |
| `src/lib/api.ts`                    | API client (axios)          |

---

## 10. Example Code Snippets

### Backend: Auth Router

```python
# app/routers/auth.py
from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/google")
async def google_auth(token_data: GoogleTokenRequest, db: Session = Depends(get_db)):
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token_data.id_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )

        email = idinfo["email"]

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user
            is_super_admin = email in settings.SUPER_ADMIN_EMAILS
            user = User(
                email=email,
                name=idinfo.get("name"),
                picture=idinfo.get("picture"),
                role="super-admin" if is_super_admin else "user",
                is_approved=is_super_admin
            )
            db.add(user)
            db.commit()

        # Generate JWT
        access_token = create_jwt_token(user)

        return {
            "user": user,
            "role": user.role,
            "is_approved": user.is_approved,
            "access_token": access_token
        }

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Frontend: NextAuth Config

```typescript
// src/lib/auth.ts
import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      // Call backend to register/verify user
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/google`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_token: account?.id_token }),
        },
      );

      if (!res.ok) return false;

      const data = await res.json();
      user.role = data.role;
      user.is_approved = data.is_approved;

      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.is_approved = user.is_approved;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.role = token.role;
      session.user.is_approved = token.is_approved;
      return session;
    },
  },
});
```

---

## 11. Security Checklist

- [ ] Verify Google ID Token on **backend** (ไม่ trust frontend)
- [ ] ใช้ HttpOnly cookies สำหรับ session
- [ ] SUPER_ADMIN_EMAILS เก็บใน ENV ไม่ใช่ในโค้ด
- [ ] Rate limiting on `/auth/google` (ป้องกัน brute force)
- [ ] CORS configuration (whitelist frontend domains)
- [ ] Input validation ทุก endpoint
- [ ] HTTPS in production
- [ ] JWT expiration (ไม่เกิน 24 ชม.)
- [ ] Secure headers (helmet/security middleware)

---

## 12. Deployment Notes

### Google Cloud Console Setup

1. สร้าง OAuth 2.0 Client ID
2. เพิ่ม Authorized JavaScript origins:
   - `http://localhost:3000` (dev)
   - `https://your-domain.com` (prod)
3. เพิ่ม Authorized redirect URIs:
   - `http://localhost:3000/api/auth/callback/google`
   - `https://your-domain.com/api/auth/callback/google`

### Cloud Run Environment

```bash
# Set environment variables
gcloud run services update SERVICE_NAME \
  --set-env-vars="GOOGLE_CLIENT_ID=xxx,SUPER_ADMIN_EMAILS=admin@company.com"
```

---

## 13. Testing Checklist

- [ ] New user login → shows pending approval page
- [ ] Super-admin email login → goes directly to admin
- [ ] Super-admin can see user list
- [ ] Super-admin can approve user
- [ ] Approved user can access admin
- [ ] Logout clears session
- [ ] Invalid token returns 401
- [ ] Non-super-admin cannot access /admin/users

---

## License

This specification is part of the JVC AI Support Platform project.  
Feel free to adapt for other projects.
