import requests
import logging
import httpx
from typing import Dict
logger = logging.getLogger(__name__)
logger = logging.getLogger("MediaMTXService")
logger.setLevel(logging.INFO)


class MediaMTXService:
    def __init__(self):
        self.api_base_url = "http://127.0.0.1:9997/v3"
        self.stream_base_url = "http://127.0.0.1:8888"
        self.rtsp_port = 8554
        self.http_port = 8888
        
    async def test_mediamtx_connection(self) -> bool:
        """Test koneksi ke MediaMTX API"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.api_base_url}/config/global/get")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"MediaMTX connection test failed: {e}")
            return False
    
    async def get_all_streams_status(self) -> Dict[str, Dict]:
        """Get status semua streams sekaligus dari /paths/list"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.api_base_url}/paths/list")
                
                if response.status_code == 200:
                    data = response.json()
                    status_map = {}
                    
                    for stream in data.get('items', []):
                        stream_key = stream['name']
                        status_map[stream_key] = {
                            "exists": True,
                            "has_source": stream.get('source') is not None,
                            "source_ready": stream.get('ready', False),
                            "is_active": stream.get('ready', False)
                        }
                    
                    return status_map
                
                return {}
                
        except Exception as e:
            logger.warning(f"Error getting all streams status: {e}")
            return {}


    async def add_stream_to_mediamtx(self, stream_key: str, rtsp_source_url: str) -> bool:
        """Register stream ke MediaMTX"""
        try:
            path_config = {
                "source": rtsp_source_url,
                "sourceProtocol": "tcp",  # Important untuk Dahua
                "sourceOnDemand": False,   # Save resources
                # "readTimeout": "15s"
            }
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{self.api_base_url}/config/paths/add/{stream_key}",
                    json=path_config,
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
    
    async def ensure_stream(self, stream_key: str, rtsp_source_url: str) -> bool:
        """Pastikan stream ada, kalau belum → add"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"{self.api_base_url}/config/paths/get/{stream_key}",
                )
            if resp.status_code == 200:
                logger.info(f"Stream {stream_key} already exists")
                return True
            else:
                return await self.add_stream_to_mediamtx(stream_key, rtsp_source_url)
        except Exception as e:
            logger.error(f"Ensure stream error {stream_key}: {e}")
            return False
        
    def generate_stream_urls(self, stream_key: str) -> Dict[str, str]:
        """Generate URLs untuk frontend"""
        return {
            # "rtsp_url": f"rtsp://localhost:{self.rtsp_port}/{stream_key}",
            "hls_url": f"http://localhost:{self.http_port}/{stream_key}/index.m3u8",
            # "webrtc_url": f"http://localhost:{self.http_port}/{stream_key}/webrtc"
        }
    
    def generate_rtsp_source_url(self, ip_address: str, username: str = "admin", password: str = "admin123") -> str:
        """Generate RTSP source URL untuk CCTV Dahua dengan format yang diberikan"""
        # Format: rtsp://admin:admin123@192.168.10.201:554/cam/realmonitor?channel=1&subtype=1
        return f"rtsp://{username}:{password}@{ip_address}:554/cam/realmonitor?channel=1&subtype=1"