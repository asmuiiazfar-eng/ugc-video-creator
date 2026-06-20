from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from httpx import AsyncClient

from app.database import get_db as _get_db
from app.models import User
from app.config import get_settings

settings = get_settings()
security = HTTPBearer()


async def get_db() -> AsyncSession:
    async for session in _get_db():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Verify JWT from Supabase and return the User."""
    token = credentials.credentials
    try:
        # Decode JWT using Supabase's public key (HS256 with Supabase JWT secret)
        # Supabase uses the anon key as the JWT secret for HS256
        payload = jwt.decode(
            token,
            settings.SUPABASE_ANON_KEY,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email", "")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except JWTError:
        # Try verifying via Supabase REST API as fallback
        try:
            async with AsyncClient() as client:
                resp = await client.get(
                    f"{settings.SUPABASE_URL}/auth/v1/user",
                    headers={
                        "apikey": settings.SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {token}",
                    },
                )
                if resp.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication token",
                    )
                user_data = resp.json()
                user_id = user_data.get("id")
                email = user_data.get("email", "")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

    # Ensure user exists in local DB
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        # Auto-create user from JWT
        user = User(id=user_id, email=email, credits=10, plan="free")
        db.add(user)
        await db.flush()

    return user