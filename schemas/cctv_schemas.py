from.base import BaseModel, datetime, Optional, Field, field_validator, ConfigDict


class CctvBase(BaseModel):
    titik_letak: str = Field(min_length=5, max_length=200)
    ip_address: str = Field(min_length=5, max_length=255)
    status: bool
    id_location: int = Field(gt=0)

class CctvCreate(CctvBase):
    pass

class CctvUpdate(BaseModel):
    titik_letak: Optional[str] = Field(None,min_length=5, max_length=200)
    ip_address: Optional[str] = Field(None,min_length=5, max_length=200)
    status: Optional[bool] = Field(None)
    id_location: Optional[int] = Field(None, gt=0 )

class CctvDelete(BaseModel):
    # message: str
    deleted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
    
class CctvResponse(CctvBase):
    id_cctv: int
    is_streaming: Optional[bool] = None
    cctv_location_name: Optional[str] = None
    created_at: Optional[datetime]= None
    updated_at: Optional[datetime]= None
    deleted_at: Optional[datetime]= None
    class Config:
        from_attributes = True

class StreamUrlsResponse(BaseModel):
    cctv_id: int
    stream_key: str
    rtsp_url: str
    hls_url: str
    is_streaming: bool
    class Config:
        from_attributes = True

# Buat schema untuk success response wrapper
class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[StreamUrlsResponse] = None  # Bisa juga menggunakan Union jika multiple types

    model_config = ConfigDict(from_attributes=True)
