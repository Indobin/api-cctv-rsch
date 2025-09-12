from.base import BaseModel, datetime, Optional, Field, field_validator, ConfigDict
from .role_schemas import Role

class UserBase(BaseModel):
    nama: str = Field(min_length=5, max_length=200)
    nip: int = Field(gt=0 )
    username: str = Field(min_length=6, max_length=200)

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=255)

class UserUpdate(BaseModel):
    nama: Optional[str] = Field(None,min_length=5, max_length=200)
    nip: Optional[int] = Field(None, gt=0 )
    username: Optional[str] = Field(min_length=6, max_length=200)
    password: Optional[str] = Field(None,min_length=6, max_length=255)

class UserDelete(BaseModel):
    # message: str
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
class UserResponse(UserBase):
    id_user: int
    id_role: int
    user_role_name: Optional[str] = None
    created_at: Optional[datetime]= None
    updated_at: Optional[datetime]= None
    deleted_at: Optional[datetime]= None
    class Config:
        from_attributes = True