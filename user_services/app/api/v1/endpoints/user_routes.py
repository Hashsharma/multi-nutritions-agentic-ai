# services/auth/app/api/v1/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from user_services.app.models.user_model import UserModel, AccountStatusModel, RoleModel, PlayerTypeModel, AuthProviderModel
from user_services.app.schemas.user import (UserOut)
# from shared.security.hash import hash_password
from typing import List
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
# from shared.security.token import Token, create_access_token, create_refresh_token, verify_token, check_role, verify_token_dependency
from datetime import timedelta
from user_services.app.utils.db import settings, get_async_session
from user_services.app.core.rabbitmq.rabbitmq_deps import DependsExtended

import random
import string
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()
import os
from dotenv import load_dotenv
import phonenumbers

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")


async def get_headers_from_message_mq(data: dict):
    """Extract headers from RabbitMQ message"""
    return data.get('headers', {})


def generate_username(first_name: str) -> str:
    # Extract the part before the '@'
    # name_part = email.split('@')[0]

    # Generate 6 random digits
    random_digits = ''.join(random.choices(string.digits, k=6))

    # Combine them
    user_name = f"{first_name}{random_digits}"

    return user_name

async def get_current_user(
    user_id: str = Header(..., alias="X-User-Id"),
    role: str = Header(None, alias="X-User-Role"),
    player_type: str = Header(None, alias="X-User-Player-Type"),
    is_active: str = Header(None, alias="X-User-Is-Active")
):
    # Optional: Logic to handle missing headers or validation
    if not user_id:
        raise HTTPException(status_code=401, detail="Identity headers missing")

    return {
        "user_id": int(user_id),
        "role": role,
        "player_type": player_type,
        "is_active": is_active
    }

@router.get("/users", response_model=UserOut)
async def read_profile(current_user: dict = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)):
    user_id = current_user.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    result = await session.execute(
        select(UserModel)
        .where(UserModel.user_id == user_id)
        .options(
            selectinload(UserModel.addresses),
            selectinload(UserModel.role),
            selectinload(UserModel.player_type),
            selectinload(UserModel.account_status),
            selectinload(UserModel.auth_provider),
            selectinload(UserModel.gender)
        )
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def format_phone_number(raw_number, region=None):
    # region is optional default country code, e.g. 'US'
    try:
        parsed_number = phonenumbers.parse(raw_number, region)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("Invalid phone number")
        return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
    except Exception as e:
        raise ValueError("Invalid phone number format")
  

@router.get("/users")
async def read_profile(current_user=Depends(get_current_user)):
    return {
        "user_id": current_user["user_id"],
        # "email": current_user["sub"],
        # "role": current_user["role"]
    }


async def get_current_user_from_rabbitmq(headers: dict = DependsExtended(get_headers_from_message_mq)):
    """Extract current user from headers"""
    user_id = headers.get('user_id')
    role = headers.get('role')
    player_type = headers.get('player_type')
    is_active = headers.get('is_active')
    
    if not user_id:
        raise Exception("Identity headers missing")
    
    return {
        "user_id": int(user_id),
        "role": role,
        "player_type": player_type,
        "is_active": is_active
    }

async def get_headers_from_message_mq(data: dict):
    """Extract headers from RabbitMQ message"""
    return data.get('headers', {})

async def get_current_user_from_rabbitmq(headers: dict = DependsExtended(get_headers_from_message_mq)):
    """Extract current user from headers"""
    user_id = headers.get('user_id')
    role = headers.get('role')
    player_type = headers.get('player_type')
    is_active = headers.get('is_active')
    
    if not user_id:
        raise Exception("Identity headers missing")
    
    return {
        "user_id": int(user_id),
        "role": role,
        "player_type": player_type,
        "is_active": is_active
    }

async def get_db_session():
    """Get database session - properly handle the async generator"""
    async for session in get_async_session():
        try:
            yield session
        finally:
            # Don't close here - let the caller handle it
            pass

# In rabbitmq_deps.py - Add this self-contained function
async def get_user_from_message(data: dict):
    """Self-contained function to get user from RabbitMQ message"""
    
    headers = data.get('headers', {})
    user_id = headers.get('user_id')
    
    if not user_id:
        raise Exception("Identity headers missing")
    
    print(f"Fetching user with ID: {user_id}")
    
    async for session in get_async_session():
        result = await session.execute(
            select(UserModel)
            .where(UserModel.user_id == int(user_id))
            .options(
                selectinload(UserModel.addresses),
                selectinload(UserModel.role),
                selectinload(UserModel.player_type),
                selectinload(UserModel.account_status),
                selectinload(UserModel.auth_provider),
                selectinload(UserModel.gender)
            )
        )
        
        user = result.scalars().first()
        
        if not user:
            raise Exception("User not found")
        
        # ✅ Pydantic v2 way
        user_out = UserOut.model_validate(user)

        # ✅ modern JSON serialization
        return user_out.model_dump(mode="json")


async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(UserModel).options(
                     selectinload(UserModel.addresses),
                     selectinload(UserModel.role),
                     selectinload(UserModel.player_type),
                     selectinload(UserModel.account_status),
                     selectinload(UserModel.gender)))
    users = result.scalars().all()
    return users
