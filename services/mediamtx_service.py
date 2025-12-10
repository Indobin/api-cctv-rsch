import asyncio
from annotated_types import Len
from httpx import ConnectError, ReadTimeout, ConnectTimeout
import subprocess
from typing import Dict, List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass
from enum import Enum
import httpx
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
    ip_address: Optional[str] = None
    error_message: Optional[str] = None

class MediaMTXService:
    def __init__(self, cctv_repository: CctvRepository, history_repository: HistoryRepository, notification_service: NotificationService):
        self.rtsp_port = 8554
        self.http_port = 8888
        self.cctv_repository = cctv_repository
        self.history_repository = history_repository
        self.notification_service = notification_service
        self._client: Optional[httpx.AsyncClient] = None
        self._connection_timeout = 5.0
        self._max_retries = 2
        # Cache untuk mencegah false offline detection
        self._offline_detection_cache: Dict[str, int] = {}  # {ip: consecutive_fail_count}
        self._offline_threshold = 2  # Baru dianggap offline setelah 2x pengecekan gagal berturut-turut
        # Gateway/Internet connectivity check
        self._gateway_check_hosts = ["8.8.8.8", "1.1.1.1"]  # Google DNS & Cloudflare DNS
        self._last_server_connectivity_check: Optional[datetime] = None
        self._server_connectivity_status: bool = True
        
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
        
    async def test_notification(self):
        result = await self.notification_service.create_notification(cctv_id=1)
        print(result)
        
    async def test_mediamtx_connection(self) -> bool:
        try:
            async with self._get_client() as client:
                response = await client.get(f"{settings.MEDIAMTX_API}/config/global/get")
                response.raise_for_status() 
                return response.status_code == 200
        except (ConnectError, ConnectTimeout, ReadTimeout) as e:
            logger.error(f"Koneksi ke MediaMTX gagal: {e}")
            return False
        except Exception as e:
            logger.error(f"MediaMTX API error: {e}")
            return False
            
    async def _ping_ip(self, ip: str, retries: int = 2) -> tuple[bool, str]:
        """
        Ping IP dengan retry mechanism untuk mengurangi false negative
        """
        for attempt in range(retries):
            try:
                proc = await asyncio.create_subprocess_exec(
                    "ping", "-c", "1", "-W", "5", ip,  # Timeout dinaikkan dari 2 ke 5 detik
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    # Reset counter jika ping berhasil
                    if ip in self._offline_detection_cache:
                        del self._offline_detection_cache[ip]
                    return True, "reachable"
                
                output = stderr.decode() + stdout.decode()
                if "Network is unreachable" in output or "network unreachable" in output.lower():
                    logger.debug(f"Network unreachable for {ip} (attempt {attempt + 1}/{retries})")
                    if attempt < retries - 1:
                        await asyncio.sleep(1)  # Wait sebelum retry
                        continue
                    return None, "network_unreachable"
                
                # Jika host down, coba lagi
                if attempt < retries - 1:
                    logger.debug(f"Ping failed for {ip}, retrying... (attempt {attempt + 1}/{retries})")
                    await asyncio.sleep(1)
                    continue
                    
            except Exception as e:
                logger.warning(f"Ping error for {ip} (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                    continue
                return None, "error"
        
        # Semua retry gagal
        return False, "host_down"
            
    async def get_all_status(self, stream_keys: Optional[List[str]] = None) -> Dict[str, StreamInfo]:
        try:
            async with self._get_client() as client:
                response = await client.get(f"{settings.MEDIAMTX_API}/paths/list")
                
                if response.status_code != 200:
                    return {}
                
                data = response.json()
                status_map = {}
                
                for stream in data.get('items', []):
                    stream_key = stream['name']
                    
                    if stream_keys and stream_key not in stream_keys:
                        continue
                    
                    has_source = stream.get('source') is not None
                    source_ready = stream.get('ready', False)
                    
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
                        last_updated=datetime.now(timezone.utc)  # Fixed typo: timezo -> timezone
                    )
                
                return status_map
        except Exception as e:
            logger.warning(f"Error getting all streams status: {e}")
            return {}        
    
    async def get_all_streams_status(self, stream_keys: Optional[List[str]] = None) -> Dict[str, StreamInfo]:
        logger.info("Cek semua status stream cctv...")
        
        check_mediamtx = await self.test_mediamtx_connection()
        if not check_mediamtx:
            logger.warning("MediaMTX API tidak dapat diakses. Skip pemeriksaan status.")
            return {}
            
        cctvs = self.cctv_repository.get_all_stream()
        status_map = {}
        status_counts = {
            StreamStatus.ACTIVE: 0,
            StreamStatus.CONNECTING: 0,
            StreamStatus.OFFLINE: 0,
            StreamStatus.INACTIVE: 0, 
        }
        
        # Ambil data MediaMTX dulu
        async with self._get_client() as client:
            response = await client.get(f"{settings.MEDIAMTX_API}/paths/list")
            data = response.json() if response.status_code == 200 else {"items": []}
    
        # Delay kecil untuk memastikan data MediaMTX up-to-date
        await asyncio.sleep(0.5)
    
        # Ping dengan retry mechanism
        ping_tasks = {
            cam.ip_address: asyncio.create_task(self._ping_ip(cam.ip_address, retries=2)) 
            for cam in cctvs
        }
        ping_results = {ip: await task for ip, task in ping_tasks.items()}
    
        for cam in cctvs:
            ip_reachable, ping_status = ping_results.get(cam.ip_address, (None, "unknown"))
            
            stream_data = next(
                (item for item in data.get("items", [])
                 if isinstance(item, dict) and item.get("name") == cam.stream_key), 
                None
            )
    
            # ACTIVE: Stream ready
            if stream_data and stream_data.get("ready", False):
                status = StreamStatus.ACTIVE
                
                latest_history = await asyncio.to_thread(
                    self.history_repository.get_latest_by_cctv, 
                    cam.id_cctv
                )
                 
                if latest_history and latest_history.service is False:
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
                        logger.info(f"CCTV {cam.titik_letak} (IP: {cam.ip_address}) kembali ONLINE")
                    except Exception as e:
                        logger.error(f"Failed to update service status for {cam.stream_key}: {e}")
            
            # CONNECTING: Tidak diubah sesuai permintaan
            elif ip_reachable and stream_data:
                status = StreamStatus.CONNECTING
                self.cctv_repository.update_streaming_status(cam.id_cctv, True)
            
            # OFFLINE: Dengan debouncing mechanism
            elif ip_reachable is False and ping_status == "host_down":
                # Increment fail counter
                self._offline_detection_cache[cam.ip_address] = \
                    self._offline_detection_cache.get(cam.ip_address, 0) + 1
                
                fail_count = self._offline_detection_cache[cam.ip_address]
                
                # Hanya set OFFLINE jika sudah gagal berturut-turut
                if fail_count >= self._offline_threshold:
                    status = StreamStatus.OFFLINE
                    
                    latest_history = await asyncio.to_thread(
                        self.history_repository.get_latest_by_cctv, 
                        cam.id_cctv
                    )
                    
                    # Improved notification cooldown logic
                    should_notify = True
                    if latest_history:
                        time_diff = (datetime.now(timezone.utc) - latest_history.created_at).total_seconds() / 60
                        
                        # Cooldown 10 menit untuk semua notifikasi (dinaikkan dari 5 menit)
                        if time_diff < 10:
                            should_notify = False
                            logger.debug(f"Cooldown aktif untuk {cam.ip_address}, skip notifikasi ({time_diff:.1f} menit)")
                    
                    if should_notify:
                        self.cctv_repository.update_streaming_status(cam.id_cctv, False)
                        try:
                            result = await self.notification_service.create_notification(cctv_id=cam.id_cctv)
                            if result.get("sent"):
                                logger.info(f"Notifikasi terkirim untuk CCTV {cam.titik_letak} (IP: {cam.ip_address})")
                            else:
                                logger.error(f"Notifikasi gagal untuk CCTV {cam.ip_address}: {result.get('error')}")
                        except Exception as e:
                            logger.error(f"Exception creating notification for {cam.ip_address}: {e}")
                    else:
                        # Tetap update status di database meski tidak kirim notifikasi
                        self.cctv_repository.update_streaming_status(cam.id_cctv, False)
                        
                    logger.warning(f"CCTV {cam.titik_letak} (IP: {cam.ip_address}) OFFLINE setelah {fail_count} kali pengecekan gagal")
                else:
                    # Masih dalam threshold, anggap CONNECTING untuk memberi kesempatan
                    status = StreamStatus.CONNECTING
                    logger.info(f"CCTV {cam.ip_address} ping gagal ({fail_count}/{self._offline_threshold}), masih dalam threshold")
                    
            else:
                if ping_status == "network_unreachable":
                    logger.warning(f"Network unreachable ke {cam.ip_address}, skip update status")
                status = StreamStatus.INACTIVE
                        
            status_counts[status] += 1
            status_map[cam.stream_key] = StreamInfo(
                stream_key=cam.stream_key,
                ip_address=cam.ip_address,
                status=status,
                has_source=stream_data is not None,
                source_ready=stream_data.get("ready", False) if stream_data else False,
                last_updated=datetime.now(timezone.utc)
            )
            
        logger.info(f"Total: {len(cctvs)} | Active: {status_counts[StreamStatus.ACTIVE]} | Connecting: {status_counts[StreamStatus.CONNECTING]} | Offline: {status_counts[StreamStatus.OFFLINE]} | Inactive: {status_counts[StreamStatus.INACTIVE]}")
        return status_map
        
    async def add_stream_to_mediamtx(self, stream_key: str, rtsp_source_url: str) -> bool:
        path_config = {
            "source": rtsp_source_url,
            "sourceProtocol": "tcp",
            "sourceOnDemand": True, 
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
                    logger.info(f"Stream {stream_key} sudah ada")
                    return True
                else:
                    logger.warning(f"Gagal membuat stream {stream_key}: {response.text}")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {stream_key}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(1)
        
        return False
            
    async def ensure_stream(self, stream_key: str, rtsp_source_url: str) -> bool:
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
        return {
            "hls_url": f"{settings.HOST_IP_FOR_CLIENT}/{stream_key}/index.m3u8",
        }
    
    @staticmethod
    def generate_rtsp_source_url(
        ip_address: str, 
        username: str = "admin", 
        password: str = "admin123",
        channel: int = 1,
        subtype: int = 1
    ) -> str:
        return f"rtsp://{username}:{password}@{ip_address}:554/cam/realmonitor?channel={channel}&subtype={subtype}"
    
class StreamService:
    def __init__(self, cctv_repository: CctvRepository, history_repository: HistoryRepository, location_repository: LocationRepository, notification_service: NotificationService):
        self.cctv_repository = cctv_repository
        self.location_repository = location_repository
        self.mediamtx_service = MediaMTXService(cctv_repository=cctv_repository, history_repository=history_repository, notification_service=notification_service)

    async def get_streams_by_location(self, location_id: int) -> Dict:
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
        
        stream_tuples = [
            (cam.stream_key, self.mediamtx_service.generate_rtsp_source_url(cam.ip_address))
            for cam in cameras
        ]
        await self.mediamtx_service.ensure_streams_batch(stream_tuples)
        
        await asyncio.sleep(1)
        
        stream_keys = [cam.stream_key for cam in cameras]
        all_status = await self.mediamtx_service.get_all_status(stream_keys)
        
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
    
    async def get_streams_by_cctv_ids(self, cctv_ids: List[int]) -> Dict:
        if not cctv_ids:
            raise HTTPException(status_code=400, detail="Daftar ID CCTV tidak boleh kosong")
        if len(cctv_ids) > 16:
            raise HTTPException(status_code=400, detail="Maksimum 16 ID CCTV yang diizinkan")
            
        cameras = self.cctv_repository.get_by_ids(cctv_ids)
        
        if not cameras:
            raise HTTPException(status_code=404, detail="Tidak ada CCTV yang ditemukan untuk ID yang diberikan.")
        
        streams_result = {
            "total_requested": len(cctv_ids),
            "total_found": len(cameras),
            "mediamtx_status": "offline",
            "cameras": []
        }
        
        mediamtx_online = await self.mediamtx_service.test_mediamtx_connection()
        streams_result["mediamtx_status"] = "online" if mediamtx_online else "offline"
     
        if not mediamtx_online:
            for cam in cameras:
                streams_result["cameras"].append({
                    "cctv_id": cam.id_cctv,
                    "titik_letak": cam.titik_letak,
                    "ip_address": cam.ip_address,
                    "stream_key": cam.stream_key,
                    "is_streaming": False,
                    "stream_urls": {},
                    "location_name": cam.nama_lokasi if hasattr(cam, 'nama_lokasi') else 'N/A' 
                })
            return streams_result

        stream_tuples = [
            (cam.stream_key, self.mediamtx_service.generate_rtsp_source_url(cam.ip_address))
            for cam in cameras
        ]
        await self.mediamtx_service.ensure_streams_batch(stream_tuples)
        
        await asyncio.sleep(1)
    
        stream_keys = [cam.stream_key for cam in cameras]
        all_status = await self.mediamtx_service.get_all_status(stream_keys)
 
        for cam in cameras:
            stream_info = all_status.get(cam.stream_key)
            is_active = stream_info.status == StreamStatus.CONNECTING if stream_info else False
            
            streams_result["cameras"].append({
                "cctv_id": cam.id_cctv,
                "titik_letak": cam.titik_letak,
                "ip_address": cam.ip_address,
                "stream_key": cam.stream_key,
                "is_streaming": is_active,
                "stream_urls": self.mediamtx_service.generate_stream_urls(cam.stream_key),
                "stream_status": stream_info.status.value if stream_info else "unknown",
                "location_name": cam.nama_lokasi if hasattr(cam, 'nama_lokasi') else 'N/A'
            })
            
        return streams_result