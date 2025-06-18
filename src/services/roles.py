from typing import List, Self
from fastapi import Depends, HTTPException, status, Request

from src.database.models import User, UserRole
from src.services.auth import auth_service


class RoleAccess:
    def __init__(self: Self, allowed_roles: List[UserRole]):
        """
        Initialize the RoleAccess object.

        Args:
        allowed_roles (List[UserRole]): The roles that are allowed to access the
        endpoint.

        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self: Self,
        request: Request,
        current_user: User = Depends(auth_service.get_current_user),
    ):
        """
        Check if the current user has the required role to access the endpoint.

        Args:
            request (Request): The request object.
            current_user (User): The current user object.

        Raises:
            HTTPException: If the user does not have the required role.

        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=403, detail="Access denied: insufficient privileges"
            )
