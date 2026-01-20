"""Authentication service."""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.user import User
from backend.app.schemas.user import UserCreate
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.audit.events import AuditEvent, AuditEventType
from backend.app.audit.audit_logger import audit_logger


async def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username
        password: Plain password

    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        # Log failed login attempt
        await audit_logger.log(AuditEvent(
            event_type=AuditEventType.USER_LOGIN_FAILED,
            actor_username=username,
            action=f"Login failed: user not found",
            success=False,
            error_message="User not found"
        ))
        return None

    if not verify_password(password, user.hashed_password):
        # Log failed login attempt
        await audit_logger.log(AuditEvent(
            event_type=AuditEventType.USER_LOGIN_FAILED,
            actor_id=user.id,
            actor_username=user.username,
            action=f"Login failed: incorrect password",
            success=False,
            error_message="Incorrect password"
        ))
        return None

    if not user.is_active:
        # Log failed login attempt
        await audit_logger.log(AuditEvent(
            event_type=AuditEventType.USER_LOGIN_FAILED,
            actor_id=user.id,
            actor_username=user.username,
            action=f"Login failed: user inactive",
            success=False,
            error_message="User inactive"
        ))
        return None

    # Log successful login
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.USER_LOGIN,
        actor_id=user.id,
        actor_username=user.username,
        action=f"User logged in successfully"
    ))

    return user


async def create_user(db: Session, user_in: UserCreate, creator: User | None = None) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        user_in: User creation data
        creator: User creating this user (for audit)

    Returns:
        Created user object
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_admin=user_in.is_admin
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log user creation
    await audit_logger.log(AuditEvent(
        event_type=AuditEventType.USER_CREATED,
        actor_id=creator.id if creator else None,
        actor_username=creator.username if creator else "system",
        resource_type="user",
        resource_id=user.id,
        action=f"Created user: {user.username}",
        details={"is_admin": user.is_admin}
    ))

    return user
