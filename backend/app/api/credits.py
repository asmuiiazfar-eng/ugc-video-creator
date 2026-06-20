from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import stripe

from app.database import get_db
from app.models import User, CreditTransaction
from app.core.deps import get_current_user
from app.core.credits import get_balance, add_credits
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/credits", tags=["credits"])

stripe.api_key = settings.STRIPE_SECRET_KEY


class BalanceResponse(BaseModel):
    balance: int


class TransactionResponse(BaseModel):
    id: str
    amount: int
    action: str
    reference_id: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


class PurchaseRequest(BaseModel):
    amount: int
    success_url: str
    cancel_url: str


class PurchaseResponse(BaseModel):
    checkout_url: str
    session_id: str


@router.get("/balance", response_model=BalanceResponse)
async def check_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current credit balance."""
    balance = await get_balance(str(current_user.id), db)
    return BalanceResponse(balance=balance)


@router.get("/history", response_model=List[TransactionResponse])
async def credit_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get credit transaction history."""
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(100)
    )
    txs = result.scalars().all()
    return [TransactionResponse(
        id=str(t.id),
        amount=t.amount,
        action=t.action,
        reference_id=t.reference_id,
        created_at=t.created_at.isoformat(),
    ) for t in txs]


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_credits(
    request: PurchaseRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe checkout session for purchasing credits."""
    try:
        # Price: $1 = 100 credits, $10 = 1000 credits, etc.
        unit_amount = 100  # $1 in cents
        quantity = request.amount

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{request.amount} Credits",
                            "description": "UGC Video Creator Credits",
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": quantity,
                }
            ],
            mode="payment",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "credits": str(request.amount),
            },
        )

        return PurchaseResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create checkout session: {str(e)}",
        )