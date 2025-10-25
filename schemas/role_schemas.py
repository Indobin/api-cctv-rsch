from.base import BaseModel

class RoleBase(BaseModel):
    nama_role: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id_role: int

    class Config:
        from_attributes =True