import logging
from fastapi import (
    APIRouter,
    status,
    BackgroundTasks,
    Request,
    Depends,
    HTTPException,
    Form,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import UserResponse, UserCreate, TokenModel, RequestEmail
from src.database.db import get_db
from src.services.users import UserService
from src.services.auth import auth_service
from src.services.email import send_email


router = APIRouter(prefix="/auth", tags=["Auth"])
logger = logging.getLogger()


@router.post(
    "/signup/", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def signup(
    user: UserCreate,
    background_task: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    This endpoint allows a new user to sign up by providing their username, email, and password.
    If the email or username is already in use, a conflict error is raised. Upon successful signup,
    an email is sent to the user for verification.

    Args:
        user (UserCreate): The user signup details including username, email, and password.
        background_task (BackgroundTasks): Background task manager for sending email.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session dependency.

    Returns:
        UserResponse: The newly created user details without the password.

    Raises:
        HTTPException: If the email or username is already in use, or if there is an error during signup.

    """
    user_service = UserService(db)
    email_user = await user_service.get_user_by_email(user.email)

    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exist",
        )
    name_user = await user_service.get_user_by_name(user.username)

    if name_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this name already exist",
        )

    user.password = auth_service.get_password_hash(user.password)
    new_user = await user_service.create_user(user)
    background_task.add_task(
        send_email, new_user.email, new_user.username, str(request.base_url)
    )
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint for users.

    This endpoint authenticates a user using their username and password.
    If the user is not found or the password is incorrect, an unauthorized error is raised.
    If the user's email is not confirmed, an unauthorized error is raised.
    If the login is successful, a JSON object is returned with the access token and token type.

    Args:
        body (OAuth2PasswordRequestForm): The login details including username and password.
        db (AsyncSession): The database session dependency.

    Returns:
        TokenModel: The JSON object with the access token and token type.

    Raises:
        HTTPException: If the user is not found, the password is incorrect, or the email is not confirmed.

    """
    user_service = UserService(db)
    user = await user_service.get_user_by_name(body.username)
    if user is None or not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirms a user's email address.

    This endpoint confirms a user's email address if the token is valid.
    If the email address is already confirmed, a success message is returned.
    If the email address is not found, a bad request error is raised.
    If the token is invalid, a bad request error is raised.

    Args:
        token (str): The token sent to the user's email address.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A JSON object with a success message.

    Raises:
        HTTPException: If the email address is not found or the token is invalid.

    """
    user_service = UserService(db)
    email = auth_service.get_email_from_token(token)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed_email:
        return {"message": "Your email is already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_task: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a confirmation email to the user.

    This endpoint allows a user to request a confirmation email to be sent to their registered email address.
    If the email is already confirmed, a message indicating the confirmation is returned.
    Otherwise, a background task is initiated to send the confirmation email.

    Args:
        body (RequestEmail): Contains the email address of the user.
        background_task (BackgroundTasks): Manages the background task for sending the email.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A JSON object with a message indicating the status of the email confirmation request.

    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user:
        if user.confirmed_email:
            return {"message": "Your email is already confirmed"}
        background_task.add_task(
            send_email, user.email, user.username, str(request.base_url)
        )
    return {"message": "Check your email for confirmation"}


@router.post("/forgot_password")
async def forgot_password(
    body: RequestEmail,
    background_task: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates the password reset process for a user.

    This endpoint allows a user to request a password reset email to be sent to their registered email address.
    If the email address is not found or not confirmed, an error is raised.
    If the email is valid and confirmed, a background task is initiated to send the password reset email.

    Args:
        body (RequestEmail): Contains the email address of the user requesting a password reset.
        background_task (BackgroundTasks): Manages the background task for sending the email.
        request (Request): The HTTP request object.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A JSON object with a message indicating the status of the password reset email request.

    Raises:
        HTTPException: If the email address is not found or the email is not confirmed.

    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if not user.confirmed_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    background_task.add_task(
        send_email, user.email, user.username, str(request.base_url), True
    )
    return {"message": "Check your email for confirmation"}


@router.get("/reset_password/{token}")
async def reset_password(token: str):
    """
    Redirects to the change password page if the password reset token is valid.

    Args:
        token (str): The password reset token.

    Returns:
        RedirectResponse: Redirects to the change password page.

    Raises:
        HTTPException: If the token is invalid.

    """
    return RedirectResponse(url=f"/change_password/{token}")


@router.post("/reset_password/{token}")
async def post_reset_password(
    token: str, password: str = Form(...), db: AsyncSession = Depends(get_db)
):
    """
    Resets a user's password using a provided token and new password.

    This endpoint allows a user to change their password if they have a valid
    password reset token. The new password is hashed and updated in the database.
    If the token is invalid or the user's email is not confirmed, an error is raised.

    Args:
        token (str): The password reset token.
        password (str): The new password provided by the user.
        db (AsyncSession): The database session dependency.

    Returns:
        dict: A JSON object with a message indicating the password change status.

    Raises:
        HTTPException: If the token is invalid, the email is not confirmed, or if
        there is an error during the reset process.

    """
    user_service = UserService(db)
    email = auth_service.get_email_from_token(token)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if not user.confirmed_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    hashed_password = auth_service.get_password_hash(password)
    await user_service.reset_password(hashed_password, email)
    return {"message": "Password successfully changed"}
