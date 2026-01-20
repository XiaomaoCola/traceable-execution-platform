"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.auth import Token, LoginRequest
from backend.app.schemas.user import UserCreate, UserMe
from backend.app.core.dependencies import DatabaseSession, CurrentUser
from backend.app.core.security import create_access_token
from backend.app.services.auth_service import authenticate_user, create_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: DatabaseSession
):
    """
    Login with username and password.

    Returns JWT access token.
    """
    user = await authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token)


@router.post("/register", response_model=UserMe)
async def register(
    user_in: UserCreate,
    db: DatabaseSession
):
    """
    Register a new user.

    Public endpoint for initial user registration.
    """
    user = await create_user(db, user_in, creator=None)
    return user


@router.get("/me", response_model=UserMe)
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return current_user
