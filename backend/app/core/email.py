"""Transactional email via Resend (Sprint 3).

All senders degrade gracefully: when ``RESEND_API_KEY`` is empty (local dev,
missing config) the call logs and returns ``False`` instead of raising. This
matches the project's "no-op when key absent" convention used for R2/Kie.ai.

Public API:
    send_email(to, subject, html) -> bool
    send_welcome_email(email) -> bool
    send_purchase_receipt_email(email, package_name, credits, amount_usd, session_id) -> bool
    send_render_complete_email(email, project_title, output_url, success) -> bool
    send_low_credits_email(email, balance) -> bool
"""

import logging
from typing import Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _client():
    """Build the Resend client lazily so the import stays cheap in dev.

    Returns ``None`` when not configured — callers treat that as a no-op.
    """
    if not settings.RESEND_API_KEY:
        return None
    try:
        import resend
    except ImportError:  # pragma: no cover - dependency not installed yet
        logger.warning("resend package not installed; skipping email send")
        return None
    resend.api_key = settings.RESEND_API_KEY
    return resend


def send_email(to: str, subject: str, html: str) -> bool:
    """Send an HTML email via Resend.

    Returns True on success, False on no-op or failure. Never raises — email
    is a best-effort side channel and should not break the request flow.
    """
    client = _client()
    if client is None:
        logger.info("[email:noop] to=%s subject=%r", to, subject)
        return False
    try:
        client.Emails.send({
            "from": settings.FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info("[email:sent] to=%s subject=%r", to, subject)
        return True
    except Exception as exc:  # pragma: no cover - network/Resend errors
        logger.warning("[email:failed] to=%s subject=%r err=%s", to, subject, exc)
        return False


def send_welcome_email(email: str) -> bool:
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">
  <h1 style="color:#7c3aed">Welcome to UGC Studio 👋</h1>
  <p>You're all set. You start with <strong>10 free credits</strong> — enough
  to render your first AI video.</p>
  <p>Head to your dashboard, pick an avatar, write a script, and hit render.
  Need more credits? Top up anytime from the billing page.</p>
  <p style="margin-top:24px;color:#6b7280">— The UGC Studio Team</p>
</div>"""
    return send_email(email, "Welcome to UGC Studio 🎬", html)


def send_purchase_receipt_email(
    email: str,
    package_name: str,
    credits: int,
    amount_usd: float,
    session_id: str,
) -> bool:
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">
  <h1 style="color:#7c3aed">Payment received ✅</h1>
  <p>Thanks for your purchase!</p>
  <table style="border-collapse:collapse;margin:16px 0">
    <tr><td style="padding:6px 12px;color:#6b7280">Package</td>
        <td style="padding:6px 12px"><strong>{package_name}</strong></td></tr>
    <tr><td style="padding:6px 12px;color:#6b7280">Credits added</td>
        <td style="padding:6px 12px"><strong>{credits}</strong></td></tr>
    <tr><td style="padding:6px 12px;color:#6b7280">Amount</td>
        <td style="padding:6px 12px"><strong>${amount_usd:.2f} USD</strong></td></tr>
    <tr><td style="padding:6px 12px;color:#6b7280">Receipt</td>
        <td style="padding:6px 12px;font-family:monospace">{session_id}</td></tr>
  </table>
  <p>Your credits are available now. Happy creating!</p>
  <p style="margin-top:24px;color:#6b7280">— The UGC Studio Team</p>
</div>"""
    return send_email(email, f"Receipt: {package_name}", html)


def send_render_complete_email(
    email: str,
    project_title: str,
    output_url: Optional[str] = None,
    success: bool = True,
) -> bool:
    status_line = "completed successfully ✅" if success else "failed ❌"
    link_block = ""
    if success and output_url:
        link_block = (
            f'<p><a href="{output_url}" style="display:inline-block;'
            'background:#7c3aed;color:#fff;padding:10px 18px;border-radius:8px;'
            'text-decoration:none">Watch your video</a></p>'
        )
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">
  <h1 style="color:#7c3aed">Your render {status_line}</h1>
  <p>Project: <strong>{project_title}</strong></p>
  {link_block}
  <p style="margin-top:24px;color:#6b7280">— The UGC Studio Team</p>
</div>"""
    subject = (
        f"Your video is ready: {project_title}"
        if success
        else f"Render failed: {project_title}"
    )
    return send_email(email, subject, html)


def send_low_credits_email(email: str, balance: int) -> bool:
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#1f2937">
  <h1 style="color:#ea580c">You're running low on credits</h1>
  <p>You have <strong>{balance}</strong> credits left. Renders cost 1 credit
  per scene — top up to keep creating without interruption.</p>
  <p><a href="#" style="color:#7c3aed">Buy more credits →</a></p>
  <p style="margin-top:24px;color:#6b7280">— The UGC Studio Team</p>
</div>"""
    return send_email(email, "You're running low on credits", html)
