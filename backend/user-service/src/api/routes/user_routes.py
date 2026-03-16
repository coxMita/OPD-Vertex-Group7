from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.api.auth import get_current_user
from src.api.dependencies import get_user_service
from src.models.dto.user_create_request import UserCreateRequest
from src.models.dto.user_dto import UserDTO
from src.models.dto.user_update_request import UserUpdateRequest
from src.services.user_service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", status_code=status.HTTP_200_OK)
def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
) -> list[UserDTO]:
    """List all users."""
    return service.list_users()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreateRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> UserDTO | dict[str, str]:
    """Create a new user."""
    try:
        return service.create_user(request)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"message": str(e)}


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> UserDTO | dict[str, str]:
    """Get a specific user by user_id."""
    user = service.get_user(user_id)
    if user is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "User not found"}
    return user


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def update_preferences(
    user_id: str,
    request: UserUpdateRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> UserDTO:
    """Update user preferences."""
    return service.update_preferences(user_id, request)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: str,
    service: Annotated[UserService, Depends(get_user_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> dict[str, str]:
    """Delete a user."""
    success = service.delete_user(user_id)
    if not success:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "User not found"}
    return {"message": "User deleted successfully"}
