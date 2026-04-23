from pydantic import BaseModel, EmailStr, constr, model_validator
from typing import List, Optional
from datetime import datetime, date
from enum import Enum

# Enums, matching those in your SQLAlchemy model
class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class AuthProviderEnum(str, Enum):
    email = "email"
    google = "google"
    facebook = "facebook"
    instagram = "instagram"
    phone = "phone"


class RoleEnum(str, Enum):
    member = "member"
    admin = "admin"

class AccountStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    banned = "banned"

class PlayerTypeEnum(str, Enum):
    admin = "admin"
    trainer = "trainer"
    member = "member"
    receptionist = "receptionist"
    coach = "coach"

# Location output schema (simplified)
class AddressOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    user_name: str
    auth_provider: AuthProviderEnum
    role: RoleEnum
    account_status: AccountStatusEnum
    created_at: datetime
    updated_at: Optional[datetime] = None
    address: List[AddressOut] = []
    player_type: Optional[PlayerTypeEnum] = None

    class Config:
        from_attributes = True



class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str

class UserCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    auth_provider: AuthProviderEnum
    addresses: Optional[List[AddressCreate]] = None

    @model_validator(mode="after")
    def validate_auth_provider(self) -> "UserCreate":
        """
        Custom validator to enforce required fields based on auth_provider.
        """
        if self.auth_provider == AuthProviderEnum.email:
            if not self.email or not self.password:
                raise ValueError("Email and password are required for email registration.")

        elif self.auth_provider == AuthProviderEnum.phone:
            if not self.phone_number:
                raise ValueError("Phone number is required for phone registration.")

        elif self.auth_provider == AuthProviderEnum.google:
            if not self.email:
                raise ValueError("Email is required for Google registration.")

        return self
        

class RequestOTP(BaseModel):
    phone_number: str


class VerifyOTP(BaseModel):
    phone_number: str
    otp: str

class Role(BaseModel):
    name: str

    class Config:
        from_attributes = True

class PlayerType(BaseModel):
    name: str

    class Config:
        from_attributes = True

class Gender(BaseModel):
    name: str

    class Config:
        from_attributes = True

class UserProfileOut(BaseModel):
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    user_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[Role] = None
    player_type: Optional[PlayerType] = None
    gender: Optional[Gender] = None

    class Config:
        from_attributes = True


class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    user_name: Optional[str] = None
    otp: Optional[str] = None
    password_hash: Optional[str] = None
    auth_provider: Optional[AuthProviderEnum] = None
    role: Optional[RoleEnum] = None
    account_status: Optional[AccountStatusEnum] = None
    player_type: Optional[PlayerTypeEnum] = None