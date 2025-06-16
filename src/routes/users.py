from fastapi import APIRouter, Depends, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import UserModel, UserResponse
from src.services.auth import auth_service
from src.services.users import UserService
from src.services.upload_file import UploadFileService
from src.database.db import get_db
from src.conf.config import settings


router = APIRouter(prefix="/users", tags=["Users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me",
    response_model=UserResponse,
    description="No more than 10 requests per minute",
)
@limiter.limit("10/minute")
async def get_me(
    request: Request, user: UserModel = Depends(auth_service.get_current_user)
):
    return user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar(
    file: UploadFile = File(),
    user: UserModel = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    avatar_url = UploadFileService(
        settings.CLOUDINARY_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ).upload_file(file, user.username)
    user_service = UserService(db)
    user = await user_service.update_avatar(user.email, avatar_url)
    return user
