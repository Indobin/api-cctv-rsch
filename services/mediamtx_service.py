import asyncio
import httpx
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
logger = logging.getLogger(__name__)
# logger = logging.getLogger("MediaMTXService")
# logger.setLevel(logging.INFO)

class StreamStatus(str, Enum):
    ACTIVE = "active"
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

class StreamEventManager:
    """Manager untuk SSE events tanpa Redis"""
    
    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, location_id: str) -> asyncio.Queue:
        """Subscribe ke stream events untuk lokasi tertentu"""
        async with self._lock:
            if location_id not in self._subscribers:
                self._subscribers[location_id] = set()
            
            queue = asyncio.Queue(maxsize=50)
            self._subscribers[location_id].add(queue)
            logger.info(f"New subscriber for location {location_id}")
            return queue
    
    async def unsubscribe(self, location_id: str, queue: asyncio.Queue):
        """Unsubscribe dari stream events"""
        async with self._lock:
            if location_id in self._subscribers:
                self._subscribers[location_id].discard(queue)
                if not self._subscribers[location_id]:
                    del self._subscribers[location_id]
                logger.info(f"Subscriber removed from location {location_id}")
    
    async def publish(self, location_id: str, event_data: Dict):
        """Publish event ke semua subscribers"""
        async with self._lock:
            if location_id not in self._subscribers:
                return
            
            dead_queues = set()
            for queue in self._subscribers[location_id]:
                try:
                    queue.put_nowait(event_data)
                except asyncio.QueueFull:
                    logger.warning(f"Queue full for location {location_id}")
                    dead_queues.add(queue)
            
            # Cleanup dead queues
            self._subscribers[location_id] -= dead_queues

class MediaMTXService:
    def __init__(self):
        self.api_base_url = "http://127.0.0.1:9997/v3"
        self.stream_base_url = "http://127.0.0.1:8888"
        self.rtsp_port = 8554
        self.http_port = 8888
        
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
        """Cleanup resources"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def test_mediamtx_connection(self) -> bool:
        """Test koneksi ke MediaMTX API"""
        try:
            async with self._get_client() as client:
                response = await client.get(f"{self.api_base_url}/config/global/get")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"MediaMTX connection test failed: {e}")
            return False
    
    async def get_all_streams_status(self, stream_keys: Optional[List[str]] = None) -> Dict[str, StreamInfo]:
        """
        Get status semua streams dengan filtering optional
        Returns StreamInfo objects untuk better type safety
        """
        try:
            async with self._get_client() as client:
                response = await client.get(f"{self.api_base_url}/paths/list")
                
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


    async def add_stream_to_mediamtx(self, stream_key: str, rtsp_source_url: str) -> bool:
        """Register stream ke MediaMTX dengan retry logic"""
        path_config = {
            "source": rtsp_source_url,
            "sourceProtocol": "tcp",
            "sourceOnDemand": True,  # Ubah ke True untuk save resources
            # "readTimeout": "15s",
            "runOnReady": "",
            "runOnRead": ""
        }
        
        for attempt in range(self._max_retries):
            try:
                async with self._get_client() as client:
                    response = await client.post(
                        f"{self.api_base_url}/config/paths/add/{stream_key}",
                        json=path_config,
                    )
                
                if response.status_code == 200:
                    logger.info(f"Stream {stream_key} registered successfully")
                    return True
                elif response.status_code == 409:
                    # Stream already exists
                    logger.info(f"Stream {stream_key} already exists")
                    return True
                else:
                    logger.warning(f"Failed to register stream {stream_key}: {response.text}")
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {stream_key}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(1)
        
        return False
    
    async def ensure_stream(self, stream_key: str, rtsp_source_url: str) -> bool:
        """Pastikan stream ada dengan idempotent operation"""
        try:
            async with self._get_client() as client:
                response = await client.get(
                    f"{self.api_base_url}/config/paths/get/{stream_key}",
                )
            if response.status_code == 200:
                logger.info(f"Stream {stream_key} already exists")
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
        """
        Batch operation untuk ensure multiple streams
        streams: List of (stream_key, rtsp_source_url) tuples
        Returns: Dict of stream_key -> success status
        """
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
    
    def __init__(self, cctv_repository: CctvRepository, location_repository: LocationRepository):
        self.cctv_repository = cctv_repository
        self.location_repository= location_repository
        self.mediamtx_service = MediaMTXService()
        self.event_manager = StreamEventManager()
    
    async def get_stream_urls(self, cctv_id: int) -> Dict:
        """Get stream URLs untuk single CCTV"""
        cctv = self.cctv_repository.get_by_id(cctv_id)
        if not cctv:
            raise HTTPException(status_code=404, detail="CCTV tidak ditemukan")
        
        # Test MediaMTX connection
        mediamtx_online = await self.mediamtx_service.test_mediamtx_connection()
        
        if not mediamtx_online:
            return {
                "cctv_id": cctv.id_cctv,
                "stream_key": cctv.stream_key,
                "stream_urls": {},
                "is_streaming": False,
                "mediamtx_status": "offline",
                "note": "MediaMTX server offline"
            }
        
        # Ensure stream exists
        rtsp_source_url = self.mediamtx_service.generate_rtsp_source_url(cctv.ip_address)
        stream_registered = await self.mediamtx_service.ensure_stream(
            cctv.stream_key,
            rtsp_source_url
        )
        
        # Get actual status
        status_map = await self.mediamtx_service.get_all_streams_status([cctv.stream_key])
        stream_info = status_map.get(cctv.stream_key)
        
        is_active = stream_info.status == StreamStatus.ACTIVE if stream_info else False
        
        # Update database
        self.cctv_repository.update_streaming_status(cctv_id, is_active)
        
        return {
            "cctv_id": cctv.id_cctv,
            "stream_key": cctv.stream_key,
            "stream_urls": self.mediamtx_service.generate_stream_urls(cctv.stream_key),
            "is_streaming": is_active,
            "mediamtx_status": "online",
            "stream_status": stream_info.status.value if stream_info else "unknown",
            "note": "Stream ready" if is_active else "Stream akan aktif ketika diakses"
        }
    
    async def get_streams_by_location(self, location_id: int) -> Dict:
        """Get all streams untuk location dengan optimized queries"""
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
            # Return basic info when MediaMTX is offline
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
        all_status = await self.mediamtx_service.get_all_streams_status(stream_keys)
        
        # Build response and update database
        for cam in cameras:
            stream_info = all_status.get(cam.stream_key)
            is_active = stream_info.status == StreamStatus.ACTIVE if stream_info else False
            
            # Update database
            self.cctv_repository.update_streaming_status(cam.id_cctv, is_active)
            
            location_streams["cameras"].append({
                "cctv_id": cam.id_cctv,
                "titik_letak": cam.titik_letak,
                "ip_address": cam.ip_address,
                "stream_key": cam.stream_key,
                "is_streaming": is_active,
                "stream_urls": self.mediamtx_service.generate_stream_urls(cam.stream_key),
                "stream_status": stream_info.status.value if stream_info else "unknown"
            })
        
        # Publish event untuk SSE subscribers
        await self.event_manager.publish(
            str(location_id),
            {
                "event": "location_streams_updated",
                "data": location_streams,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return location_streams
    
    async def stream_location_events(self, location_id: int):
        """
        SSE endpoint untuk realtime stream updates
        Usage: GET /streams/location/{location_id}/events
        """
        queue = await self.event_manager.subscribe(str(location_id))
        
        async def event_generator():
            try:
                # Send initial connection message
                yield f"data: {json.dumps({'event': 'connected', 'location_id': location_id})}\n\n"
                
                while True:
                    # Wait for events with timeout
                    try:
                        event_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield f"data: {json.dumps(event_data)}\n\n"
                    except asyncio.TimeoutError:
                        # Send heartbeat
                        yield f"data: {json.dumps({'event': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                        
            except asyncio.CancelledError:
                logger.info(f"SSE connection cancelled for location {location_id}")
            finally:
                await self.event_manager.unsubscribe(str(location_id), queue)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    async def monitor_streams_background(self, location_id: int, interval: int = 10):
        """
        Background task untuk monitoring streams dan push updates via SSE
        Jalankan ini sebagai background task di startup
        """
        while True:
            try:
                streams_data = await self.get_streams_by_location(location_id)
                # Event sudah di-publish di get_streams_by_location
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error monitoring location {location_id}: {e}")
                await asyncio.sleep(interval)