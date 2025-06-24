from fastapi import FastAPI
from app.api.routes import router
from app.db.database import engine
from app.db.base import Base
import asyncio

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router)
