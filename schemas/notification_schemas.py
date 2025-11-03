from.base import BaseModel, Optional
from datetime import datetime

class NotificationResponse(BaseModel):
    id_notification: int
    id_history: int
    id_cctv: int
    created_at: datetime
    note: Optional[str]
    titik_letak: str
    ip_address: str

    class Config:
    
        from_attributes = True