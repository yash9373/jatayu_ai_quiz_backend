from sqlalchemy.future import select
from app.models.user import User

async def get_user_by_email(db, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_id(db, user_id: int):
    """Get user by user_id"""
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()