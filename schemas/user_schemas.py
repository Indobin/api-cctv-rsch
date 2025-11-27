from.base import BaseModel, datetime, Optional, Field, StringConstraints
from typing import Annotated
NIK_Type = Annotated[
    str, 
    StringConstraints(
        min_length=9, 
        max_length=11, 
        pattern=r'^\d{4,5}\.\d{5,6}$'
    )
]
class UserBase(BaseModel):
    nama: str = Field(min_length=5, max_length=50)
    nik: NIK_Type = Field(description="NIK harus berupa 10-11 digit angka")
    username: str = Field(min_length=5, max_length=50)
    id_role: int

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=255)

class UserCheck(BaseModel):
    nama: str = Field(min_length=5, max_length=50)
    nik: NIK_Type = Field(description="NIK harus berupa 10-11 digit angka")
    username: str = Field(min_length=5, max_length=50)
    password: str = Field(min_length=6, max_length=255)
class UserUpdate(BaseModel):
    nama: Optional[str] = Field(None,min_length=5, max_length=50)
    username: Optional[str] = Field(None,min_length=5, max_length=50)
    nik: Optional[NIK_Type] = Field(None, description="NIK harus berupa 10-11 digit angka")
    password: Optional[str] = Field(None,min_length=6, max_length=255)
    id_role: Optional[int] = Field(None, gt=0)

class UserResponse(UserBase):
    id_user: int
    id_role: int
    user_role_name: Optional[str] = None
    created_at: Optional[datetime]= None
    last_login: Optional[datetime]= None
    deleted_at: Optional[datetime]= None
    class Config:
        from_attributes = True