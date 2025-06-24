import asyncio
from app.db.database import engine
from app.db.base import Base
from app.models import user, revoked_token  # Import all models here

async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Drop all tables
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(create_all())
