"""
Email sending utility. Uses SMTP if configured, logs to console otherwise.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER)


def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Send an email. Returns True on success, False on failure."""
    if not _smtp_configured():
        logger.info("[EMAIL DEV] To: %s | Subject: %s", to, subject)
        logger.info("[EMAIL DEV] Body: %s", text or html)
        return True  # treat as success in dev

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to

    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        return False


def send_password_reset(to: str, token: str) -> bool:
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <p>You requested a password reset for your PolymarketIQ account.</p>
    <p><a href="{reset_url}">Reset your password</a></p>
    <p>This link expires in 1 hour. If you did not request this, ignore this email.</p>
    <p style="color:#888;font-size:12px">Reset URL: {reset_url}</p>
    """
    text = f"Reset your password: {reset_url}\n\nExpires in 1 hour."
    return send_email(to, "Reset your PolymarketIQ password", html, text)


def send_waitlist_confirmation(to: str) -> bool:
    html = """
    <p>You're on the PolymarketIQ waitlist!</p>
    <p>We'll email you as soon as your access is ready.</p>
    <p style="color:#888;font-size:12px">PolymarketIQ — Prediction Market Intelligence</p>
    """
    text = "You're on the PolymarketIQ waitlist. We'll email you when your access is ready."
    return send_email(to, "You're on the PolymarketIQ waitlist", html, text)
