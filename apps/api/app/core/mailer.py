"""Simple mailer: file-backed in development, SMTP optional."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_email(*, to: str, subject: str, body: str) -> str:
    """Send email and return delivery channel description."""
    settings = get_settings()
    if settings.smtp_host:
        msg = EmailMessage()
        msg["From"] = settings.mail_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_user:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return "smtp"

    out_dir = Path(settings.upload_dir) / "mail"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = to.replace("@", "_at_")
    path = out_dir / f"{safe}_{subject[:40].replace(' ', '_')}.txt"
    path.write_text(f"To: {to}\nSubject: {subject}\n\n{body}", encoding="utf-8")
    logger.info("Dev mail written to %s", path)
    return f"file:{path}"
