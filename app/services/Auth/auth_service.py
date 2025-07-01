from app.models.user import User, UserRole
from app.models.revoked_token import RevokedToken
from app.core.security import verify_password, get_password_hash, decode_token
from app.repositories.user_repo import get_user_by_email
from app.core.config import settings
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
from app.db.database import get_db
from app.services.Auth.AuthInterface import IAuthService

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class AuthService(IAuthService):
    async def login(self, email: str, password: str, db):
        user = await get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + access_token_expires
        jti = str(uuid.uuid4())
        to_encode = {"sub": user.email, "exp": expire, "jti": jti}
        from jose import jwt  # Local import to avoid circular import issues
        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return {
            "token": token,
            "role": user.role,
            "user_id": user.user_id
        }

    async def signup(self, data: dict, db):
        user = await get_user_by_email(db, data["email"])
        if user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
        hashed_password = get_password_hash(data["password"])
        
        # Role is now required
        if "role" not in data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role is required")
            
        role_str = data["role"]
        try:
            role = UserRole(role_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
            
        new_user = User(
            name=data["name"],
            email=data["email"],
            hashed_password=hashed_password,
            role=role
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return str(new_user.user_id)

    async def logout(self, token: str = None, db: AsyncSession = Depends(get_db)):
        if token:
            payload = decode_token(token)
            jti = payload.get("jti")
            if jti:
                revoked = RevokedToken(jti=jti)
                db.add(revoked)
                await db.commit()
        return {"message": "Successfully logged out."}

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    jti = payload.get("jti")
    if jti:
        result = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=401, detail="Token has been revoked. Please log in again.")
    user = await get_user_by_email(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user