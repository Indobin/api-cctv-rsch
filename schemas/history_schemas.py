from.base import BaseModel, Optional, datetime, Field

class HistoryBase(BaseModel):
    id_cctv: int = Field(gt=0)
    note: str = Field(None,min_length=5, max_length=255)

class HistoryCreate(HistoryBase):
    pass

class HistoryUpdate(BaseModel):
    service: Optional[bool]
    note: Optional[str] = Field(None,min_length=5, max_length=255)

class HistoryResponse(HistoryBase):
    id_history: int
    service: bool
    created_at: Optional[datetime]= None
    cctv_name: Optional[str] = None
    class Config:
        from_attributes =True