#!/usr/bin/env python3
"""
Initialize the database and create a default admin user
"""
import os
import sys
from sqlmodel import Session, select

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, init_db
from app.models import User, CompanySetting
from app.auth import get_password_hash

def create_admin_user():
    """Create a default admin user if one doesn't exist"""
    init_db()
    
    with Session(engine) as session:
        # Check if admin user already exists
        admin_user = session.exec(
            select(User).where(User.role == "ADMIN")
        ).first()
        
        if not admin_user:
            print("Creating default admin user...")
            admin = User(
                username="admin",
                email="admin@pvapp.local",
                role="ADMIN",
                hashed_password=get_password_hash("admin123")
            )
            session.add(admin)
            session.commit()
            print("✓ Admin user created")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠️  Please change the password after first login!")
        else:
            print("✓ Admin user already exists")
        
        # Create default VAT rate setting if it doesn't exist
        vat_setting = session.exec(
            select(CompanySetting).where(CompanySetting.key == "vat_rate")
        ).first()
        
        if not vat_setting:
            print("Creating default VAT rate setting...")
            vat = CompanySetting(
                key="vat_rate",
                value="19.0",
                description="VAT rate percentage (Romania default)"
            )
            session.add(vat)
            session.commit()
            print("✓ VAT rate setting created (19%)")
        else:
            print("✓ VAT rate setting already exists")
        
        print("\n✓ Database initialization complete!")

if __name__ == "__main__":
    create_admin_user()
