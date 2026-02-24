# ─────────────────────────────────────────────
#  delivery.py  —  Sends email to subscribers
# ─────────────────────────────────────────────

import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_SENDER, EMAIL_PASSWORD, SUBSCRIBERS, NEWSLETTER_NAME


def send_email(html: str, plain: str) -> None:
    today   = date.today().strftime("%B %d, %Y")
    subject = f"{NEWSLETTER_NAME} — {today}"

    print(f"  [delivery] Sending to {len(SUBSCRIBERS)} subscriber(s)...")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)

        for recipient in SUBSCRIBERS:
            msg            = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = EMAIL_SENDER
            msg["To"]      = recipient

            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html,  "html"))

            server.sendmail(EMAIL_SENDER, recipient, msg.as_string())
            print(f"  [delivery] Sent to {recipient}")

    print("  [delivery] Done.")
