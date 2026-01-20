"""User model."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from backend.app.db.base import Base, IDMixin, TimestampMixin


class User(Base, IDMixin, TimestampMixin):
    """
    User model for authentication and authorization.

    Roles:
    - is_admin=False: employee (can submit tickets, upload artifacts, trigger proof runs)
    - is_admin=True: admin (can manage assets, scripts, approve action runs, view all audit logs)
    """

    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Relationships
    tickets = relationship("Ticket", back_populates="creator", foreign_keys="Ticket.created_by_id")
    runs = relationship("Run", back_populates="executor", foreign_keys="Run.executed_by_id")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', is_admin={self.is_admin})>"
