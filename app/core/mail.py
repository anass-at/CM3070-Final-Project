import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings


def send_password_reset_email(to_email: str, reset_link: str, name: str = ""):
    """Send a password reset email via SMTP (MailHog in development)."""
    greeting = f"Hi {name}," if name else "Hello,"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px; color: #333;">
      <h2 style="color: #0d6efd; margin-bottom: 4px;">NatID</h2>
      <p style="color: #666; margin-top: 0; font-size: 13px;">National Identity Platform</p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 16px 0;">

      <p>{greeting}</p>
      <p>We received a request to reset the password for your NatID account. Click the button below to choose a new password.</p>

      <div style="text-align: center; margin: 32px 0;">
        <a href="{reset_link}"
           style="background: #0d6efd; color: #fff; padding: 12px 28px; border-radius: 6px;
                  text-decoration: none; font-weight: bold; display: inline-block;">
          Reset My Password
        </a>
      </div>

      <p style="font-size: 13px; color: #888;">
        This link expires in <strong>1 hour</strong>. If you did not request a password reset,
        you can safely ignore this email — your password will not change.
      </p>

      <p style="font-size: 12px; color: #aaa;">
        If the button above doesn't work, copy and paste this link into your browser:<br>
        <a href="{reset_link}" style="color: #0d6efd;">{reset_link}</a>
      </p>

      <hr style="border: none; border-top: 1px solid #eee; margin: 16px 0;">
      <p style="font-size: 11px; color: #bbb; text-align: center;">
        NatID — National Identity Platform &nbsp;|&nbsp; Do not reply to this email
      </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your NatID password"
    msg["From"]    = settings.MAIL_FROM
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.MAIL_HOST, settings.MAIL_PORT) as smtp:
        smtp.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
