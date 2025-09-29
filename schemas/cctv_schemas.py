from.base import BaseModel, datetime, Optional, Field, field_validator, ConfigDict
from ipaddress import IPv4Address

class CctvBase(BaseModel):
    titik_letak: str = Field(min_length=3, max_length=200)
    ip_address: str = Field(
        description="Alamat IPv4 yang valid.",
        min_length=7, # e.g., "0.0.0.0"
        max_length=15, # e.g., "255.255.255.255"
    )
    @field_validator('ip_address')
    @classmethod
    def validate_ip_format(cls, v):
        try:
            IPv4Address(v)
            return v
        except ValueError:
            raise ValueError('ip_address harus berupa format IPv4 yang valid.')
    id_location: int = Field(gt=0)

class CctvCreate(CctvBase):
    pass

class CctvUpdate(BaseModel):
    titik_letak: Optional[str] = Field(None,min_length=3, max_length=200)
    ip_address: Optional[str] = Field(
        None,
        description="Alamat IPv4 yang valid.",
        min_length=7, 
        max_length=15, 
    )
    id_location: Optional[int] = Field(None, gt=0 )
    @field_validator("ip_address")
    @classmethod
    def validate_ip_format(cls, v):
        if v is None:
            return v
        try:
            IPv4Address(v)
            return v
        except ValueError:
            raise ValueError("ip_address harus berupa format IPv4 yang valid.")

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
    # status: str = "success"
    message: str
    data: Optional[StreamUrlsResponse] = None  

    model_config = ConfigDict(from_attributes=True)
