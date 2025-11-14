from.base import BaseModel, datetime, Optional, Field
class UserBase(BaseModel):
    nama: str = Field(min_length=5, max_length=200)
    nip: int = Field(gt=0, min_length=18, max_length=18)
    username: str = Field(min_length=6, max_length=200)

class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=255)

class UserUpdate(BaseModel):
    nama: Optional[str] = Field(None,min_length=5, max_length=200)
    nip: Optional[int] = Field(None, gt=0, min_length=18, max_length=18)
    username: Optional[str] = Field(None, min_length=6, max_length=200)
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