#!/usr/bin/env python3
"""
Database Permissions Fixer

This script fixes PostgreSQL permissions for the jatayu_ai_quiz_backend project.
Run this script once to set up proper permissions for your database user.
"""

import os
import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env file")
    sys.exit(1)

print(f"Database URL: {DATABASE_URL}")

async def fix_permissions():
    """Fix database permissions for the current user."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL)
        
        async with engine.connect() as connection:
            # Get current user
            result = await connection.execute(text("SELECT current_user"))
            current_user = result.fetchone()[0]
            print(f"Current database user: {current_user}")
            
            # Get database name
            result = await connection.execute(text("SELECT current_database()"))
            current_db = result.fetchone()[0]
            print(f"Current database: {current_db}")
            
            print("\n🔧 Setting up database permissions...")
            
            # Fix permissions for current user
            permission_queries = [
                f"GRANT USAGE, CREATE ON SCHEMA public TO {current_user}",
                f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {current_user}",
                f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {current_user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {current_user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {current_user}",
                f"GRANT ALL PRIVILEGES ON DATABASE {current_db} TO {current_user}"
            ]
            
            for query in permission_queries:
                try:
                    await connection.execute(text(query))
                    print(f"✅ {query}")
                except Exception as e:
                    print(f"⚠️  {query} - {e}")
            
            # Commit changes
            await connection.commit()
            print("\n✅ Database permissions setup completed!")
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Error setting up permissions: {e}")
        print("\n🔧 Manual fix needed:")
        print("Connect to PostgreSQL as a superuser and run:")
        print(f"GRANT USAGE, CREATE ON SCHEMA public TO {current_user if 'current_user' in locals() else 'your_user'};")
        print(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {current_user if 'current_user' in locals() else 'your_user'};")
        print(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {current_user if 'current_user' in locals() else 'your_user'};")
        return False

def check_connection():
    """Check if we can connect to the database."""
    try:
        # Try sync connection first (simpler)
        sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        engine = create_engine(sync_url)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking database connection...")
    
    if check_connection():
        print("\n🔧 Attempting to fix permissions...")
        asyncio.run(fix_permissions())
        
        print("\n🚀 You can now run your migrations:")
        print("alembic upgrade head")
    else:
        print("\n❌ Cannot connect to database. Please check your DATABASE_URL and database server.")