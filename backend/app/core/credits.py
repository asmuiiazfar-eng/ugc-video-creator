from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models import User, CreditTransaction
from app.config import get_settings

settings = get_settings()


async def get_balance(user_id: str, db: AsyncSession) -> int:
    """Get the current credit balance for a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return 0
    return user.credits


async def deduct_credits(user_id: str, amount: int, db: AsyncSession, reference_id: str | None = None) -> bool:
    """Deduct credits from a user's balance. Returns True if successful, False if insufficient."""
    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if user is None or user.credits < amount:
        return False

    user.credits -= amount
    db.add(user)

    tx = CreditTransaction(
        user_id=user_id,
        amount=-amount,
        action="usage",
        reference_id=reference_id,
    )
    db.add(tx)
    await db.flush()
    return True


async def add_credits(user_id: str, amount: int, db: AsyncSession, action: str = "bonus", reference_id: str | None = None) -> int:
    """Add credits to a user's balance. Returns the new balance."""
    result = await db.execute(
        select(User).where(User.id == user_id).with_for_update()
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise ValueError(f"User {user_id} not found")

    user.credits += amount
    db.add(user)

    tx = CreditTransaction(
        user_id=user_id,
        amount=amount,
        action=action,
        reference_id=reference_id,
    )
    db.add(tx)
    await db.flush()
    return user.credits


async def refund_credits(user_id: str, amount: int, db: AsyncSession, reference_id: str | None = None) -> int:
    """Refund credits to a user. Returns the new balance."""
    return await add_credits(user_id, amount, db, action="refund", reference_id=reference_id)