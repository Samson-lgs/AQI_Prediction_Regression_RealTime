import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER or 'no-reply@example.com')
SMTP_TLS = os.getenv('SMTP_TLS', 'true').lower() in ('1', 'true', 'yes')


def send_email(to_address: str, subject: str, body: str, html: Optional[str] = None) -> bool:
    """
    Send an email using SMTP credentials from environment variables.

    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM (optional)
    Returns True on success, False on configuration issues.
    """
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        # Not configured; treat as no-op success in non-production to avoid crashes
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = SMTP_FROM
    msg['To'] = to_address
    msg['Subject'] = subject

    text_part = MIMEText(body, 'plain')
    msg.attach(text_part)
    if html:
        html_part = MIMEText(html, 'html')
        msg.attach(html_part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        if SMTP_TLS:
            server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_address], msg.as_string())
    return True
