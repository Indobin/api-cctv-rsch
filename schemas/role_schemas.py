from.base import BaseModel, datetime

class RoleBase(BaseModel):
    type: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_aattributes =True