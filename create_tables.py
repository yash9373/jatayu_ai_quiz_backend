import asyncio
from app.db.database import engine
from app.db.base import Base
from app.models import user, revoked_token, test  # Import all models here
from sqlalchemy import text

async def create_all():
    async with engine.begin() as conn:
        # Drop all tables and types with CASCADE to handle dependencies
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text('DROP TABLE IF EXISTS "user" CASCADE'))
        await conn.execute(text('DROP TABLE IF EXISTS "test" CASCADE'))
        await conn.execute(text("DROP TABLE IF EXISTS revoked_tokens CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
        
        # Create new schema
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_all())
