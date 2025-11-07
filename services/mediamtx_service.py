import asyncio
from annotated_types import Len
from httpx import ConnectError, ReadTimeout, ConnectTimeout
import subprocess
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException
from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass
from enum import Enum
import httpx
from starlette.types import StatefulLifespan
from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from repositories.history_repository import HistoryRepository
from core.config import settings
from services.notification_service import NotificationService
logger = logging.getLogger(__name__)

class StreamStatus(str, Enum):
    ACTIVE = "active"
    OFFLINE = "offline"
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ERROR = "error" 
    
@dataclass
class StreamInfo:
    stream_key: str
    status: StreamStatus
    has_source: bool
    source_ready: bool
    last_updated: datetime
    error_message: Optional[str] = None

class MediaMTXService:
    def __init__(self, cctv_repository: CctvRepository, history_repository: HistoryRepository, notification_service: NotificationService):
        self.rtsp_port = 8554
        self.http_port = 8888
        self.cctv_repository = cctv_repository
        self.history_repository = history_repository
        self.notification_service = notification_service
        # Connection pooling untuk efisiensi
        self._client: Optional[httpx.AsyncClient] = None
        self._connection_timeout = 5.0
        self._max_retries = 2
    @asynccontextmanager
    async def _get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._connection_timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        try:
            yield self._client
        except Exception as e:
            logger.error(f"Http client error: {e}")
            raise

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        
    # Di endpoint atau test file
    async def test_notification(self):
        result = await self.notification_service.create_notification(
            cctv_id=1,
            # note="Test notification"
        )
        print(result)
    async def test_mediamtx_connection(self) -> bool:
        """Test koneksi ke MediaMTX API"""
        try:
            async with self._get_client() as client:
                response = await client.get(f"{settings.MEDIAMTX_API}/config/global/get")
                response.raise_for_status() 
                return response.status_code == 200
        except (ConnectError, ConnectTimeout, ReadTimeout) as e:
            logger.error(f"❌ Koneksi ke MediaMTX gagal (Network/Timeout): {e}")
            return False
        except Exception as e:
            logger.error(f"❌ MediaMTX API returned an error (Status Code): {e}")
            return False
    async def _ping_ip(self, ip: str) -> bool:
        """Ping IP CCTV untuk melihat status CCTV"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "2", ip,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception as e:
            logger.warning(f"Ping failed for {ip}: {e}")
            return False
            
    async def get_all_status(self, stream_keys: Optional[List[str]] = None) -> Dict[str, StreamInfo]:
            """
            Cek status cctv lewat mediamtx
            """
            try:
                async with self._get_client() as client:
                    response = await client.get(f"{settings.MEDIAMTX_API}/paths/list")
                    
                    if response.status_code != 200:
                        return {}
                    
                    data = response.json()
                    status_map = {}
                    for stream in data.get('items', []):
                        stream_key = stream['name']
                        
                        # Filter jika stream_keys diberikan
                        if stream_keys and stream_key not in stream_keys:
                            continue
                        
                        has_source = stream.get('source') is not None
                        source_ready = stream.get('ready', False)
                        
                        # Determine status
                        if source_ready:
                            status = StreamStatus.ACTIVE
                        elif has_source:
                            status = StreamStatus.CONNECTING
                        else:
                            status = StreamStatus.INACTIVE
                        
                        status_map[stream_key] = StreamInfo(
                            stream_key=stream_key,
                            status=status,
                            has_source=has_source,
                            source_ready=source_ready,
                            last_updated=datetime.now()
                        )
                    
                    return status_map
            except Exception as e:
                logger.warning(f"Error getting all streams status: {e}")
                return {}        
    
    async def get_all_streams_status(self, stream_keys: Optional[List[str]] = None) -> Dict[str, StreamInfo]:
        """Cek status cctv lewat mediamtx dan kirim notif"""
        logger.info(" Cek semua status stream cctv...")
        check_mediamtx = await self.test_mediamtx_connection()
        if not check_mediamtx:
            logger.warning("MediaMTX API tidak dapat diakses. Pemeriksaan status streaming untuk semua CCTV dihentikan.")
            return {}
            
        cctvs = self.cctv_repository.get_all()
        status_map = {}
        status_counts = {
                StreamStatus.ACTIVE: 0,
                StreamStatus.CONNECTING: 0,
                StreamStatus.OFFLINE: 0,
            }
        async with self._get_client() as client:
            response = await client.get(f"{settings.MEDIAMTX_API}/paths/list")
            data = response.json() if response.status_code == 200 else {"items": []}
    
        ping_tasks = {cam.ip_address: asyncio.create_task(self._ping_ip(cam.ip_address)) for cam in cctvs}
        ping_results = {ip: await task for ip, task in ping_tasks.items()}
    
        for cam in cctvs:
            ip_reachable = ping_results.get(cam.ip_address, False)
       
            stream_data = next(
                (item for item in data.get("items", [])
                 
                 if isinstance(item, dict) and item.get("name") == cam.stream_key), 
                None
            )
    
            if stream_data and stream_data.get("ready", False):
                status = StreamStatus.ACTIVE
                
                latest_history = await asyncio.to_thread(
                     self.history_repository.get_latest_by_cctv, 
                     cam.id_cctv
                 )
                 
                if latest_history and latest_history.service is False:
                    # Update service jadi True karena CCTV sudah online kembali
                    try:
                        await asyncio.to_thread(
                            self.history_repository.update_service_status,
                            latest_history.id_history,
                            True
                        )
                        await asyncio.to_thread(
                            self.cctv_repository.update_streaming_status,
                            cam.id_cctv,
                            True
                        )
                        logger.info(f"CCTV {cam.titik_letak} (IP: {cam.ip_address}) kembali ONLINE. Service status updated.")
                    except Exception as e:
                        logger.error(f"❌ Failed to update service status for {cam.stream_key}: {e}", exc_info=True)
            elif ip_reachable:
                status = StreamStatus.CONNECTING
                # if self.cctv_repository.update_streaming_status(cam.id_cctv, True):
                #     logger.info(f"CCTV {cam.titik_letak} (IP: {cam.ip_address}) kembali CONNECTING. Streaming status updated.")
                # else:
                #     logger.error(f"❌ Failed to update streaming status for {cam.stream_key}")
            else:
                status = StreamStatus.OFFLINE
                if self.notification_service:
                    # note = f"CCTV {cam.titik_letak} (IP: {cam.ip_address}) terdeteksi OFFLINE. Perangkat tidak terjangkau."
                    self.cctv_repository.update_streaming_status(cam.id_cctv, False)
                    try:
                        result = await self.notification_service.create_notification(
                            cctv_id=cam.id_cctv
                            # note=note
                        )
                        if result.get("sent"):
                            logger.info(f"Notifikasi berhasil dikirim dari ip cctv {cam.ip_address}")
                        else:
                            logger.error(f"❌ Notifikasi tidak jadi dikirim dari ip cctv {cam.ip_address}: {result.get('error')}")
                    except Exception as e:
                        logger.error(f"❌ Exception creating notification for ip {cam.ip_address}: {e}", exc_info=True)
                        
            status_counts[status] += 1
            status_map[cam.stream_key] = StreamInfo(
                stream_key=cam.stream_key,
                status=status,
                has_source=stream_data is not None,
                # count=count(status),
                source_ready=stream_data.get("ready", False) if stream_data else False,
                last_updated=datetime.now()
            )
        logger.info("========================================")
        logger.info(f"Total CCTV: {len(cctvs)}")
        logger.info(f"Status Active: {status_counts[StreamStatus.ACTIVE]}")
        logger.info(f"Status Connecting: {status_counts[StreamStatus.CONNECTING]}")
        logger.info(f"Status Offline: {status_counts[StreamStatus.OFFLINE]}")
        logger.info("========================================")
        return status_map
        
   
    async def add_stream_to_mediamtx(self, stream_key: str, rtsp_source_url: str) -> bool:
            """Register stream ke MediaMTX dengan retry logic"""
            path_config = {
                "source": rtsp_source_url,
                "sourceProtocol": "tcp",
                "sourceOnDemand": True,  # Ubah ke True untuk save resources
                "runOnReady": "",
                "runOnRead": ""
            }
            
            for attempt in range(self._max_retries):
                try:
                    async with self._get_client() as client:
                        response = await client.post(
                            f"{settings.MEDIAMTX_API}/config/paths/add/{stream_key}",
                            json=path_config,
                        )
                    
                    if response.status_code == 200:
                        logger.info(f"Stream {stream_key} berhasil dibuat")
                        return True
                    elif response.status_code == 409:
                        # Stream already exists
                        logger.info(f"Stream {stream_key} sudah ada")
                        return True
                    else:
                        logger.warning(f" Gagal membuat stream {stream_key}: {response.text}")
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for {stream_key}: {e}")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(1)
            
            return False
            
    async def ensure_stream(self, stream_key: str, rtsp_source_url: str) -> bool:
        """Memastikan stream ada di patch mediamtx"""
        try:
            async with self._get_client() as client:
                response = await client.get(
                    f"{settings.MEDIAMTX_API}/config/paths/get/{stream_key}",
                )
            if response.status_code == 200:
                logger.info(f"Stream {stream_key} sudah ada")
                return True
            elif response.status_code == 404:
                return await self.add_stream_to_mediamtx(stream_key, rtsp_source_url)
            else:
                logger.warning(f"Unexpected response for {stream_key}: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Ensure stream error {stream_key}: {e}")
            return False
    
    async def ensure_streams_batch(self, streams: List[tuple[str, str]]) -> Dict[str, bool]:
        """Batch operation untuk ensure multiple streams"""
        tasks = [
            self.ensure_stream(stream_key, rtsp_url) 
            for stream_key, rtsp_url in streams
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            streams[i][0]: isinstance(results[i], bool) and results[i]
            for i in range(len(streams))
        }

    def generate_stream_urls(self, stream_key: str) -> Dict[str, str]:
        """Generate URLs untuk frontend"""
        return {
            # "rtsp_url": f"rtsp://localhost:{self.rtsp_port}/{stream_key}",
            "hls_url": f"http://localhost:{self.http_port}/{stream_key}/index.m3u8",
            # "webrtc_url": f"http://localhost:{self.http_port}/{stream_key}/webrtc"
        }
    
    @staticmethod
    def generate_rtsp_source_url(
        ip_address: str, 
        username: str = "admin", 
        password: str = "admin123",
        channel: int = 1,
        subtype: int = 1
    ) -> str:
        """Generate RTSP source URL untuk CCTV Dahua"""
        return f"rtsp://{username}:{password}@{ip_address}:554/cam/realmonitor?channel={channel}&subtype={subtype}"
    
class StreamService:
    """Service layer untuk stream operations"""
    
    def __init__(self, cctv_repository: CctvRepository,history_repository: HistoryRepository,  location_repository: LocationRepository, notification_service: NotificationService):
        self.cctv_repository = cctv_repository
        self.location_repository= location_repository
        self.mediamtx_service = MediaMTXService(cctv_repository=cctv_repository, history_repository=history_repository, notification_service=notification_service)

    async def get_streams_by_location(self, location_id: int) -> Dict:
        """Melakukan streams berdasarkan lokasi cctv"""
        existing_location = self.location_repository.get_by_id(location_id)
        if not existing_location:
            raise HTTPException(status_code=400, detail="Lokasi tidak ditemukan")
        
        cameras = self.cctv_repository.get_by_location(location_id).all()
        
        mediamtx_online = await self.mediamtx_service.test_mediamtx_connection()
        
        location_streams = {
            "location_id": location_id,
            "location_name": existing_location.nama_lokasi,
            "total_cameras": len(cameras),
            "mediamtx_status": "online" if mediamtx_online else "offline",
            "cameras": []
        }
        
        if not mediamtx_online:
            for cam in cameras:
                location_streams["cameras"].append({
                    "cctv_id": cam.id_cctv,
                    "titik_letak": cam.titik_letak,
                    "ip_address": cam.ip_address,
                    "stream_key": cam.stream_key,
                    "is_streaming": False,
                    "stream_urls": {}
                })
            return location_streams
        
        # Batch ensure streams
        stream_tuples = [
            (cam.stream_key, self.mediamtx_service.generate_rtsp_source_url(cam.ip_address))
            for cam in cameras
        ]
        await self.mediamtx_service.ensure_streams_batch(stream_tuples)
        
        # Wait for streams to initialize
        await asyncio.sleep(1)
        
        # Get status for all streams in location
        stream_keys = [cam.stream_key for cam in cameras]
        all_status = await self.mediamtx_service.get_all_status(stream_keys)
        
        # Build response and update database
        for cam in cameras:
            stream_info = all_status.get(cam.stream_key)
            is_active = stream_info.status == StreamStatus.CONNECTING if stream_info else False
            
            location_streams["cameras"].append({
                "cctv_id": cam.id_cctv,
                "titik_letak": cam.titik_letak,
                "ip_address": cam.ip_address,
                "stream_key": cam.stream_key,
                "is_streaming": is_active,
                "stream_urls": self.mediamtx_service.generate_stream_urls(cam.stream_key),
                "stream_status": stream_info.status.value if stream_info else "unknown"
            })
        
        return location_streams
    
