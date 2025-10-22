from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class NotificationResponse(BaseModel):
    notification_id: int
    history: Optional[Dict] = None
    cctv: Optional[Dict] = None
    
    class Config:
        from_attributes = True
        

class WebhookDisconnect(BaseModel):
    stream_key: str
    metadata: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "stream_key": "cctv_stream_001",
                "metadata": {"reason": "Connection timeout"}
            }
        }


class WebhookConnect(BaseModel):
    stream_key: str
    metadata: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "stream_key": "cctv_stream_001",
                "metadata": {"source": "rtsp"}
            }
        }