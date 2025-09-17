from.base import BaseModel, datetime

class RoleBase(BaseModel):
    nama_role: str

class RoleCreate(RoleBase):
    pass

class Role(RoleBase):
    id_role: int

    class Config:
        from_aattributes =True