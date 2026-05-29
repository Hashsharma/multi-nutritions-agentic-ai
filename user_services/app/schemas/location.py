from pydantic import BaseModel
from typing import Optional
from datetime import datetime
class AddressBase(BaseModel):
    name: str
    address: Optional[str] = None

class AddressCreate(AddressBase):
    pass

class AddressOut(AddressBase):
    address_id: int

    class Config:
        orm_mode = True



class UserAddressCreate(BaseModel):
    label: str
    address_line1: str
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    state: str
    country: str
    zipcode: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_default: bool = False


class UserAddressUpdate(BaseModel):
    # label: Optional[LabelEnum] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zipcode: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_default: Optional[bool] = None


class UserAddressRead(UserAddressCreate):
    address_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserAddressAll(UserAddressCreate):
    address_id: int  
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class LatitudeLongitude(BaseModel):
    latitude: str
    longitude: str