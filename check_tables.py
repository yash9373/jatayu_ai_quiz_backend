#!/usr/bin/env python3
"""Check database tables and structure"""

import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Create a sync engine for checking
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql+asyncpg"):
    # Convert to sync postgresql
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")

sync_engine = create_engine(DATABASE_URL, echo=False)

def check_tables():
    print("=== Database Tables ===")
    
    # Get table names
    with sync_engine.connect() as conn:
        result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result]
        
    print("Tables found:")
    for table in tables:
        print(f"- {table}")
    
    # Check specific table schemas
    inspector = inspect(sync_engine)
    
    for table_name in ['users', 'user', 'tests']:
        if table_name in tables:
            print(f"\n=== {table_name} table structure ===")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"- {col['name']}: {col['type']} (nullable: {col['nullable']})")
            
            # Check foreign keys
            fks = inspector.get_foreign_keys(table_name)
            if fks:
                print(f"Foreign keys in {table_name}:")
                for fk in fks:
                    print(f"- {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

if __name__ == "__main__":
    try:
        check_tables()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure PostgreSQL is running and the database exists")
