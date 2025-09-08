from.base import BaseModel, datetime, Optional, Field, field_validator
from .role_schemas import Role

class UserBase(BaseModel):
    name: str = Field(min_length=5, max_length=200)
    username: str = Field(min_length=6)

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    user_type_id: int
    user_type_name: Optional[str]
    created_at: Optional[datetime]= None
    updated_at: Optional[datetime]= None

    class Config:
        from_attributes = True