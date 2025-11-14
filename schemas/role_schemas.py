from.base import BaseModel, Field

class RoleBase(BaseModel):
    nama_role: str = Field(min_length=5, max_length=50)

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id_role: int

    class Config:
        from_attributes =True