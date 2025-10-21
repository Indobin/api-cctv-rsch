from.base import BaseModel, Optional, datetime, Field

class HistoryBase(BaseModel):
    service: bool
    note: Optional[str]

class HistoryCreate(HistoryBase):
    pass

class HistoryUpdate(BaseModel):
    service: Optional[bool]
    note: Optional[str] = Field(None,min_length=5, max_length=255)

class HistoryResponse(HistoryBase):
    id_history: int
    id_cctv: int
    created_at: Optional[datetime]= None
    cctv_name: Optional[str] = None
    class Config:
        from_aattributes =True