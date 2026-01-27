#!/usr/bin/env python3
"""Add missing admin users to the database."""

import uuid
from datetime import datetime
from database import SessionLocal
from models import AdminUser

def add_admin_users():
    db = SessionLocal()
    
    users_to_add = [
        {
            "email": "sukrittakhan@gmail.com",
            "name": "Sukrit Takhan",
        },
        {
            "email": "chirakit.lim@gmail.com", 
            "name": "Chirakit Lim",
        },
    ]
    
    for user_data in users_to_add:
        email = user_data["email"]
        
        # Check if user exists
        user = db.query(AdminUser).filter(AdminUser.email == email).first()
        
        if user:
            print(f"User {email} already exists. Approving...")
            user.is_approved = True
            db.commit()
            print(f"✅ Approved: {email}")
        else:
            new_user = AdminUser(
                id=str(uuid.uuid4()),
                email=email,
                name=user_data["name"],
                role="admin",
                is_approved=True,
                created_at=datetime.utcnow(),
                last_login=None
            )
            db.add(new_user)
            db.commit()
            print(f"✅ Created admin user: {email}")
    
    # List all users
    print("\n--- All Admin Users ---")
    all_users = db.query(AdminUser).all()
    for u in all_users:
        print(f"  {u.email} | role: {u.role} | approved: {u.is_approved}")
    
    db.close()

if __name__ == "__main__":
    add_admin_users()
