# models/user_model.py

from sqlalchemy import String, DateTime, Date, Enum as SQLEnum, func, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from typing import List, Optional
from enum import Enum
from .base import Base  # Your SQLAlchemy declarative base
from .location import AddressModel, TimestampMixin  # 👈 Import for relationship
import enum




class GenderModel(Base, TimestampMixin):
    """Stores gender options (e.g., male, female, other)"""
    __tablename__ = "gender"
    gender_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)


class AccountStatusModel(Base, TimestampMixin):
    """Stores user account statuses (e.g., active, suspended, deleted)"""
    __tablename__ = "account_status"
    account_status_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)


class AuthProviderModel(Base, TimestampMixin):
    """Stores authentication provider options (e.g., email, google, phone)"""
    __tablename__ = "auth_providers"
    auth_provider_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


class RoleModel(Base, TimestampMixin):
    """Stores user roles (e.g., admin, trainer, member)"""
    __tablename__ = "roles"
    role_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


class PlayerTypeModel(Base, TimestampMixin):
    """Stores user player types (e.g., Beginner, Expert, Grand Master)"""
    __tablename__ = "player_types"
    player_type_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


# ---------------- Main User Table ---------------- #

class UserModel(Base, TimestampMixin):
    """Stores user information"""
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    # otp: Mapped[str] = mapped_column(String(6), nullable=True)
    # password_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Foreign keys
    gender_id: Mapped[Optional[int]] = mapped_column(ForeignKey("gender.gender_id"), nullable=True)
    auth_provider_id: Mapped[int] = mapped_column(ForeignKey("auth_providers.auth_provider_id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=True)
    account_status_id: Mapped[int] = mapped_column(ForeignKey("account_status.account_status_id"), nullable=True)
    player_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player_types.player_type_id"), nullable=True)

    # Relationships
    gender: Mapped[Optional["GenderModel"]] = relationship()
    auth_provider: Mapped["AuthProviderModel"] = relationship()
    role: Mapped["RoleModel"] = relationship()
    account_status: Mapped["AccountStatusModel"] = relationship()
    player_type: Mapped[Optional["PlayerTypeModel"]] = relationship()

    addresses: Mapped[List["AddressModel"]] = relationship(
        "AddressModel", back_populates="user", cascade="all, delete-orphan"
    )
