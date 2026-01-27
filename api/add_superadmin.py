
import uuid
from datetime import datetime
from database import SessionLocal
from models import AdminUser

def add_superadmin():
    db = SessionLocal()
    email = "mr.phariyawit@gmail.com"
    
    # Check if user exists
    user = db.query(AdminUser).filter(AdminUser.email == email).first()
    
    if user:
        print(f"User {email} already exists.")
        user.role = "super-admin"
        user.is_approved = True
        db.commit()
        print(f"Updated {email} to super-admin.")
    else:
        new_user = AdminUser(
            id=str(uuid.uuid4()),
            email=email,
            name="Phariyawit Chaiparitte",
            role="super-admin",
            is_approved=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.add(new_user)
        db.commit()
        print(f"Created super-admin user: {email}")
    
    db.close()

if __name__ == "__main__":
    add_superadmin()
