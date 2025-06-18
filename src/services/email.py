from pathlib import Path
import traceback

from fastapi_mail import ConnectionConfig, MessageSchema, MessageType, FastMail

from src.conf.config import settings
from src.services.auth import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: str, username: str, host: str, param: bool = False):
    """
    Sends an email to a user with a link to confirm their email.

    Args:
        email (str): The email address of the user.
        username (str): The username of the user.
        host (str): The host URL of the application.
        param (bool, optional): Whether to include a parameter in the URL. Defaults to False.

    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "fullname": username,
                "token": token_verification,
                "param": param,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        print("Sending email to:", email)
        await fm.send_message(message, template_name="email_template.html")
        print("Email sent!")
    except Exception as err:
        print("Email error:", err)
        traceback.print_exc()
