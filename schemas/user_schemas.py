from.base import BaseModel, datetime, Optional, Field, StringConstraints
from typing import Annotated
NIP_Type = Annotated[
    str, 
    StringConstraints(
        min_length=18, 
        max_length=18, 
        pattern=r'^\d{18}$'
    )
]
class UserBase(BaseModel):
    nama: str = Field(min_length=5, max_length=50)
    nip: NIP_Type = Field(description="NIP harus berupa 18 digit angka")
    username: str = Field(min_length=5, max_length=50)

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=255)

class UserUpdate(BaseModel):
    nama: Optional[str] = Field(None,min_length=5, max_length=50)
    username: Optional[str] = Field(None,min_length=5, max_length=50)
    nip: Optional[NIP_Type] = Field(None, description="NIP harus berupa 18 digit angka")
    password: Optional[str] = Field(None,min_length=6, max_length=255)

class UserResponse(UserBase):
    id_user: int
    id_role: int
    user_role_name: Optional[str] = None
    created_at: Optional[datetime]= None
    last_login: Optional[datetime]= None
    deleted_at: Optional[datetime]= None
    class Config:
        from_attributes = True