import redis
import pickle
from typing import Self
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.conf.config import settings
from src.services.users import UserService
from src.database.db import get_db
from src.database.models import User
from src.database.models import UserRole
from src.conf.config import settings


class Auth:
    ALGORITHM = settings.JWT_ALGORITHM

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

    def verify_password(self: Self, plain_password: str, hashed_password: str):
        """
        Verifies a plain text password against a hashed password.

        Args:
            plain_password (str): The plain text password to verify.
            hashed_password (str): The hashed password to compare against.

        Returns:
            bool: True if the plain password matches the hashed password, False otherwise.

        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self: Self, password: str):
        """
        Hashes a password using a secure hashing algorithm.

        Args:
            password (str): The plain text password to hash.

        Returns:
            str: The hashed version of the password.

        """
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: float = 15):
        """
        Creates a JWT access token with specified data and expiration time.

        Args:
            data (dict): The data to include in the token payload.
            expires_delta (float, optional): The time in minutes until the token expires. Defaults to 15 minutes.

        Returns:
            str: The encoded JWT access token.

        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"}
        )
        encoded_access_token = jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=self.ALGORITHM
        )
        return encoded_access_token

    def create_email_token(self, data: dict):
        """
        Creates a JWT token with specified data and expiration time.

        Args:
            data (dict): The data to include in the token payload.

        Returns:
            str: The encoded JWT access token.

        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update(
            {"iat": datetime.utcnow(), "exp": expire, "scope": "email_token"}
        )
        token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=self.ALGORITHM)
        return token

    async def get_current_user(
        self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        """
        Retrieves the current user from the database or cache using a JWT access token.

        This function decodes the JWT token to extract the user's email and retrieves
        the corresponding user object from the cache or database. If the token is invalid,
        the email cannot be extracted, or the user is not found, an HTTP 401 Unauthorized
        exception is raised.

        Args:
            token (str, optional): The JWT access token provided by the client.
            db (Session): The database session dependency.

        Returns:
            User: The user object associated with the provided token.

        Raises:
            HTTPException: If the token is invalid, the email cannot be extracted, or the user
            is not found in the cache or database.

        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            # Decode JWT
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[self.ALGORITHM]
            )
            if payload.get("scope") == "access_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user_service = UserService(db)
        user = self.r.get(f"user:{email}")
        if user is None:
            user = await user_service.get_user_by_email(email)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)

        if user is None:
            raise credentials_exception
        return user

    def get_email_from_token(self, token: str):
        """
        Extracts the email address from a JWT token.

        This method decodes a JWT token to extract the email address associated with it.
        The token must have a valid email scope to successfully retrieve the email.
        If the token is invalid or the scope is incorrect, an HTTP exception is raised.

        Args:
            token (str): The JWT token from which the email is to be extracted.

        Returns:
            str: The email address extracted from the token.

        Raises:
            HTTPException: If the token is invalid, has an incorrect scope, or cannot be processed.

        """
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET, algorithms=[self.ALGORITHM]
            )
            if payload["scope"] == "email_token":
                email = payload["sub"]
                return email
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid scope for token",
            )
        except JWTError as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid token for email verification",
            )


auth_service = Auth()
