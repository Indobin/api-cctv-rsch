from pydantic import BaseModel
from datetime import datetime

class NotificationResponse(BaseModel):
    id_notification: int
    id_history: int
    id_cctv: int
    created_at: datetime
    note: str
    titi_letak: str
    ip_address: str

    class Config:
    
        from_attributes = True