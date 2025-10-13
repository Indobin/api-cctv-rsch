from.base import BaseModel, datetime, Field, Optional

class LocationBase(BaseModel):
    nama_lokasi: str = Field(min_length=5, max_length=200)

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    nama_lokasi: Optional[str] = Field(None, min_length=5, max_length=200)

class LocationDelete(BaseModel):
    deleted_at: Optional[datetime] = None
    class Config:
        from_attributes =True

class LocationResponse(LocationBase):
    id_location: int

    class Config:
        from_attributes =True
