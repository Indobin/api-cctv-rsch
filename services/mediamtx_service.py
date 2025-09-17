import requests
import logging
from fastapi import HTTPException, status
from core.config import settings

logger = logging.getLogger(__name__)

class MediaMTXService:
    def __init__(self):
        self.base_url = settings.MEDIAMTX_API_URL
        self.base_url = settings.MEDIAMTX_API_USERNAME
        self.password = settings.MEDIAMTX_API_PASSWORD
        self.rtsp_port = settings.MEDIAMTX_RTSP_PORT
        self.http_port = settings.MEDIAMTX_HTTP_PORT
        self.host = settings.MEDIAMTX_HOST

    def generate_rtsp_url(self, ip_address: str):
        """Generate RTSP URL untuk CCTV Dahua"""
        return f"rtsp://admin:admin123@{ip_address}:554/cam/realmonitor?channel=1&subtype=1"
    
    def setup_stream(self, cctv_id: int, ip_address:str):
        """Setup stream di MediaMTX"""
        stream_key = f"cctv_{cctv_id}"
        rtsp_source_url = self.generate_rtsp_url(ip_address)

        try:
            # Konfigurasi path di MediaMTX
            paylaod = {
                "name": stream_key,
                "source": "rtsp",
                "sourceProtocol": "tcp",  # Gunakan TCP untuk stability
                "sourceOnDemand": True,   # Stream hanya ketika ada yang menonton
                "sourceRedirect": rtsp_source_url,
                "maxReaders": 10,         # Maksimal 10 concurrent viewers
            }

            response = requests.put(
                f"{self.base_url}/v3/config/paths/add/{stream_key}",
                json=paylaod,
                auth=(self.username, self.password),
                timeout=10
            )

            if response.status_code in [200, 201]:
               return {
                    "stream_key": stream_key,
                    "rtsp_url": f"rtsp://{self.host}:{self.rtsp_port}/{stream_key}",
                    "hls_url": f"http://{self.host}:{self.http_port}/{stream_key}/index.m3u8"
                }
            else:
                logger.error(f"MediaMTX setup failed: {response.status_code} - {response.text}")

                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"MediaMTX connection error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Media server tidak dapat diakses"
            )
    
    def remove_stream(self, stream_key: str):
        """Hapus stream dari MediaMTX"""
        try:
            response = requests.delete(
                f"{self.base_url}/v3/config/paths/delete/{stream_key}",
                auth=(self.username, self.password),
                timeout=5
            )
            return response.status_code in [200, 204]
        except requests.exceptions.RequestException as e:
            logger.error(f"MediaMTX delete error: {e}")
            return False
        
    def get_stream_status(self, stream_key: str):
        """Dapatkan status stream dari MediaMTX"""
        try:
            response = requests.get(
                f"{self.base_url}/v3/paths/get/{stream_key}",
                auth=(self.username, self.password),
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("ready", False)
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"MediaMTX status error: {e}")
            return False

    def get_all_streams(self):
        """Dapatkan semua stream yang aktif di MediaMTX"""
        try:
            response = requests.get(
                f"{self.base_url}/v3/paths/list",
                auth=(self.username, self.password),
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"MediaMTX list error: {e}")
            return []