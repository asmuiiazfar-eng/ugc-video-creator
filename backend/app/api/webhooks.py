"""Stripe webhook receiver (Sprint 3).

Listens for ``checkout.session.completed`` events, idempotently credits the
purchasing user, and emails a receipt. Idempotency is enforced by checking for
an existing ``CreditTransaction`` with the Stripe session id as its
``reference_id`` — Stripe may redeliver events, so double-crediting would
otherwise be possible.

Uses the request body's raw bytes (``Request.body``) for signature
verification, since FastAPI's JSON body parsing would consume the stream.
"""

import logging

import stripe
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy import select

from app.database import async_session_factory
from app.models import User, CreditTransaction
from app.core.credits import add_credits, CREDIT_PACKAGES
from app.core.email import send_purchase_receipt_email
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

stripe.api_key = settings.STRIPE_SECRET_KEY


async def _process_checkout_completed(session_obj) -> None:
    """Credit the user for a completed Stripe checkout session.

    Idempotent: if a transaction with this Stripe session id already exists we
    bail out. Runs in its own DB session and commits explicitly (the webhook
    handler is not a FastAPI dependency-injected route, so ``get_db``'s auto-
    commit does not apply).
    """
    session_id = session_obj.get("id")
    metadata = session_obj.get("metadata") or {}
    user_id = metadata.get("user_id")
    credits_str = metadata.get("credits")
    plan = metadata.get("plan", "")

    if not user_id or not credits_str:
        logger.warning(
            "stripe webhook: session %s missing user_id/credits metadata",
            session_id,
        )
        return

    try:
        credits = int(credits_str)
    except (TypeError, ValueError):
        logger.warning("stripe webhook: bad credits metadata %r", credits_str)
        return

    amount_total = session_obj.get("amount_total", 0)
    amount_usd = (amount_total or 0) / 100.0
    package_name = CREDIT_PACKAGES.get(plan, {}).get("name", "Credit Pack")

    # Look up the user's email once for the receipt; default to "" so the send
    # no-ops gracefully if the user somehow can't be found.
    async with async_session_factory() as db:
        # Idempotency guard: has this session already been credited?
        existing = await db.execute(
            select(CreditTransaction).where(
                CreditTransaction.reference_id == session_id
            )
        )
        if existing.scalar_one_or_none() is not None:
            logger.info("stripe webhook: session %s already credited, skipping", session_id)
            return

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            logger.warning("stripe webhook: user %s not found for session %s", user_id, session_id)
            return

        await add_credits(
            str(user.id), credits, db,
            action="purchase",
            reference_id=session_id,
        )
        await db.commit()

        email = user.email
        new_balance = user.credits

    # Email is best-effort and outside the DB transaction.
    if email:
        send_purchase_receipt_email(
            email, package_name, credits, amount_usd, session_id,
        )
    logger.info(
        "stripe webhook: credited %d to user %s (balance now %d) session=%s",
        credits, user_id, new_balance, session_id,
    )


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Receive and dispatch Stripe webhook events.

    Returns 400 on signature/verification failure and 204 on successful
    processing (or deliberate no-op, e.g. unhandled event type). Stripe treats
    any non-2xx as a retry trigger, so we only error on genuine failures.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("stripe webhook: STRIPE_WEBHOOK_SECRET not set, ignoring event")
        return {"received": False, "reason": "webhook secret not configured"}

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as exc:
        # Invalid payload
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid payload: {exc}")
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid signature: {exc}")

    event_type = event.get("type", "")
    logger.info("stripe webhook: received event %s", event_type)

    if event_type == "checkout.session.completed":
        await _process_checkout_completed(event["data"]["object"])

    # Other event types are acknowledged but ignored — Stripe only needs a 200.
    return {"received": True, "type": event_type}
