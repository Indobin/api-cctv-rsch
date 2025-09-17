from.base import BaseModel, datetime, Field

class LocationBase(BaseModel):
    nama_lokasi: str = Field(min_length=5, max_length=200)

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id_location: int

    class Config:
        from_aattributes =True