#!/usr/bin/env python3
"""
Database initialization script
Creates all tables and initial data
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal
from models import Base, User, SystemSettings
from auth_utils import get_password_hash

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@company.com").first()
        
        if not admin_user:
            admin_user = User(
                email="admin@company.com",
                name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                department="IT",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created!")
            print("   Email: admin@company.com")
            print("   Password: admin123")
            print("   ⚠️  Please change the password after first login!")
        else:
            print("ℹ️  Admin user already exists")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def create_default_settings():
    """Create default system settings"""
    db = SessionLocal()
    try:
        settings_to_create = [
            {
                "key": "ai_model",
                "value": "gpt-4",
                "description": "OpenAI model to use for responses"
            },
            {
                "key": "max_tokens",
                "value": 1000,
                "description": "Maximum tokens for AI responses"
            },
            {
                "key": "temperature",
                "value": 0.7,
                "description": "AI response creativity (0.0 to 1.0)"
            },
            {
                "key": "require_email_verification",
                "value": True,
                "description": "Require email verification for new users"
            },
            {
                "key": "enable_google_oauth",
                "value": True,
                "description": "Enable Google OAuth login"
            }
        ]
        
        for setting_data in settings_to_create:
            existing = db.query(SystemSettings).filter(
                SystemSettings.key == setting_data["key"]
            ).first()
            
            if not existing:
                setting = SystemSettings(**setting_data)
                db.add(setting)
        
        db.commit()
        print("✅ Default system settings created!")
        
    except Exception as e:
        print(f"❌ Error creating default settings: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing Enterprise Knowledge Assistant Database...")
    print("=" * 60)
    
    try:
        # Create tables
        create_tables()
        
        # Create admin user
        create_admin_user()
        
        # Create default settings
        create_default_settings()
        
        print("=" * 60)
        print("✅ Database initialization completed successfully!")
        print("\n📋 Next steps:")
        print("1. Start the backend server: uvicorn main:socket_app --reload")
        print("2. Start the frontend: cd frontend && npm run dev")
        print("3. Login as admin and upload some documents")
        print("4. Start asking questions!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()