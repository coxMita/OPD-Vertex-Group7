import asyncio
import sys

from src.config import settings
from src.email_sender import send_email


async def main() -> None:
    """Run a test email sending script."""
    recipient = settings.SMTP_FROM_EMAIL
    if recipient == "YOUR_GMAIL_ADDRESS@gmail.com" or not recipient:
        print("Error: SMTP_FROM_EMAIL is not set properly in .env.")
        sys.exit(1)

    print(f"Sending test email to: {recipient}...")
    try:
        await send_email(
            to_email=recipient,
            subject="Test from OPD-Vertex",
            message=(
                "This is a test email sent from the newly configured email service."
            ),
            is_html=False,
        )
        print("Test email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
