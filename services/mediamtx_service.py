import requests
import logging
from fastapi import HTTPException, status
from core.config import settings
from typing import Dict, Optional
from requests.auth import HTTPBasicAuth
logger = logging.getLogger(__name__)

logger = logging.getLogger("MediaMTXService")
logger.setLevel(logging.INFO)


class MediaMTXService:
    def __init__(self):
        self.api_base_url = "http://127.0.0.1:9997/v3"
        self.stream_base_url = "http://127.0.0.1:8888"
        self.rtsp_port = 8554
        self.http_port = 8888
        
    def test_mediamtx_connection(self) -> bool:
        """Test koneksi ke MediaMTX API"""
        try:
            response = requests.get(f"{self.api_base_url}/config/global/get", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"MediaMTX connection test failed: {e}")
            return False
    
    def add_stream_to_mediamtx(self, stream_key: str, rtsp_source_url: str) -> bool:
        """Register stream ke MediaMTX"""
        try:
            path_config = {
                "source": rtsp_source_url,
                "sourceProtocol": "tcp",  # Important untuk Dahua
                "sourceOnDemand": True,   # Save resources
                # "readTimeout": "15s"
            }
            
            response = requests.post(
                f"{self.api_base_url}/config/paths/add/{stream_key}",
                json=path_config,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Stream {stream_key} registered successfully")
                return True
            else:
                logger.warning(f"Stream {stream_key} auto-create mode: {response.text}")
                return False
                
        except Exception as e:
            logger.warning(f"Stream {stream_key} will auto-create: {e}")
            return False
    
    def generate_stream_urls(self, stream_key: str) -> Dict[str, str]:
        """Generate URLs untuk frontend"""
        return {
            "rtsp_url": f"rtsp://localhost:{self.rtsp_port}/{stream_key}",
            "hls_url": f"http://localhost:{self.http_port}/{stream_key}/index.m3u8",
            "webrtc_url": f"http://localhost:{self.http_port}/{stream_key}/webrtc"
        }
    
    def generate_rtsp_source_url(self, ip_address: str, username: str = "admin", password: str = "admin123") -> str:
        """Generate RTSP source URL untuk CCTV Dahua dengan format yang diberikan"""
        # Format: rtsp://admin:admin123@192.168.10.201:554/cam/realmonitor?channel=1&subtype=1
        return f"rtsp://{username}:{password}@{ip_address}:554/cam/realmonitor?channel=1&subtype=1"