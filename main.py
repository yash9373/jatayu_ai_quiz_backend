from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.db.database import engine
from app.db.base import Base
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()



import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Start scheduler only if this is the main process (not in every worker)

import os
import logging
logger = logging.getLogger(__name__)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)



@app.on_event("startup")
async def on_startup():
    # Scheduler logic removed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router)
