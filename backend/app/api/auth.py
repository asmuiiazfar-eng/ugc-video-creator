from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient as HTTPXClient
from typing import Optional

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.core.deps import get_current_user
from app.core.email import send_welcome_email

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    """Issue 6 fix: payload for Google OAuth sign-in.

    The frontend obtains a Google ID token (via Supabase OAuth or the Google
    Identity SDK) and sends it here. We verify it against Google's tokeninfo
    endpoint and upsert the local user.
    """

    id_token: str
    access_token: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserResponse(BaseModel):
    id: str
    email: str
    credits: int
    plan: str


@router.post("/signup", response_model=AuthResponse)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Sign up a new user via Supabase Auth."""
    async with HTTPXClient() as client:
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/signup",
            headers={
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            json={
                "email": request.email,
                "password": request.password,
            },
        )
        if resp.status_code != 200:
            detail = resp.json().get("msg", "Signup failed")
            raise HTTPException(status_code=resp.status_code, detail=detail)

        data = resp.json()

    user_id = data.get("user", {}).get("id", "")
    email = data.get("user", {}).get("email", request.email)

    # Create user in local DB
    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if not existing:
        user = User(id=user_id, email=email, credits=10, plan="free")
        db.add(user)
        await db.flush()
        # Sprint 3: send welcome email to new signups (best-effort).
        send_welcome_email(email)

    return AuthResponse(
        access_token=data.get("access_token", ""),
        user_id=user_id,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in with email and password via Supabase Auth."""
    async with HTTPXClient() as client:
        resp = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                "apikey": settings.SUPABASE_ANON_KEY,
                "Content-Type": "application/json",
            },
            json={
                "email": request.email,
                "password": request.password,
            },
        )
        if resp.status_code != 200:
            detail = resp.json().get("msg", "Login failed")
            raise HTTPException(status_code=resp.status_code, detail=detail)

        data = resp.json()

    user_id = data.get("user", {}).get("id", "")

    # Ensure user exists in local DB
    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if not existing:
        email = data.get("user", {}).get("email", request.email)
        user = User(id=user_id, email=email, credits=10, plan="free")
        db.add(user)
        await db.flush()

    return AuthResponse(
        access_token=data.get("access_token", ""),
        user_id=user_id,
    )


@router.post("/google", response_model=AuthResponse)
async def google_login(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Issue 6 fix: Google OAuth login.

    Verifies the Google ID token via Google's tokeninfo endpoint, then upserts
    the user in the local DB (with 10 free credits for new accounts). The
    Supabase access token (if provided) is returned for downstream API calls;
    otherwise the Google ID token itself is returned.
    """
    # 1. Verify the Google ID token
    tokeninfo_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    async with HTTPXClient() as client:
        resp = await client.get(
            tokeninfo_url,
            params={"id_token": request.id_token},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")

        payload = resp.json()

    # 2. Optional: validate audience matches our client id
    if settings.GOOGLE_CLIENT_ID:
        aud = payload.get("aud")
        if aud and aud != settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Google token audience mismatch")

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=400, detail="Google token missing sub/email")

    # 3. Upsert the local user
    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if not existing:
        user = User(id=user_id, email=email, credits=10, plan="free")
        db.add(user)
        await db.flush()
        # Sprint 3: send welcome email to new Google sign-ins (best-effort).
        send_welcome_email(email)

    # 4. Return the access token (prefer Supabase token if provided)
    return AuthResponse(
        access_token=request.access_token or request.id_token,
        user_id=user_id,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        credits=current_user.credits,
        plan=current_user.plan.value if hasattr(current_user.plan, "value") else current_user.plan,
    )