from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from pydantic import Field


# -----------------------------
# Reference / Lookup Schemas
# -----------------------------

class GenderOut(BaseModel):
    gender_id: int
    name: str

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    role_id: int
    name: str

    class Config:
        from_attributes = True


class AccountStatusOut(BaseModel):
    account_status_id: int
    name: str

    class Config:
        from_attributes = True


class AuthProviderOut(BaseModel):
    auth_provider_id: int
    name: str

    class Config:
        from_attributes = True


class PlayerTypeOut(BaseModel):
    player_type_id: int
    name: str

    class Config:
        from_attributes = True


# -----------------------------
# Address Schema
# -----------------------------

class AddressOut(BaseModel):
    address_id: int
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None

    class Config:
        from_attributes = True


# -----------------------------
# User Schema (Final Response)
# -----------------------------

class UserOut(BaseModel):
    user_id: int

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    user_name: str

    is_phone_verified: bool
    is_email_verified: Optional[bool] = None
    email_verify_otp: Optional[str] = None

    # Relationships
    gender: Optional[GenderOut] = None
    auth_provider: AuthProviderOut
    role: Optional[RoleOut] = None
    account_status: Optional[AccountStatusOut] = None
    player_type: Optional[PlayerTypeOut] = None

    addresses: List[AddressOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True