import asyncio
from app.db.database import engine

async def check_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_connection())
