from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import stripe

from app.database import get_db
from app.models import User, CreditTransaction
from app.core.deps import get_current_user
from app.core.credits import get_balance, add_credits, CREDIT_PACKAGES
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


class CheckoutRequest(BaseModel):
    """Sprint 3: frontend contract for the credit-package checkout flow.

    ``plan`` must be one of the keys in ``CREDIT_PACKAGES`` (starter/creator/pro).
    The success/cancel URLs let the browser return to the right dashboard state
    after the Stripe redirect.
    """

    plan: str
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    url: str
    session_id: str


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout_package(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Sprint 3: create a Stripe Checkout session for a fixed credit package.

    Unlike the legacy ``/purchase`` endpoint (which priced arbitrary credit
    amounts), this serves the predefined packages in ``CREDIT_PACKAGES``. The
    webhook credits the user after payment succeeds.

    Returns 503 when Stripe is not configured (matches the project's graceful-
    degradation pattern).
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credit purchases are not configured on this server.",
        )

    package = CREDIT_PACKAGES.get(request.plan)
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown plan '{request.plan}'. "
                   f"Available: {', '.join(sorted(CREDIT_PACKAGES))}.",
        )

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": package["name"],
                            "description": f"{package['credits']} UGC Studio credits",
                        },
                        "unit_amount": package["price_cents"],
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(current_user.id),
                "plan": request.plan,
                "credits": str(package["credits"]),
            },
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {str(e)}",
        )

    return CheckoutResponse(url=session.url, session_id=session.id)