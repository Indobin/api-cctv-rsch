from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from services.mediamtx_service import MediaMTXService, StreamService
from core.auth import all_roles
from core.response import success_response

router = APIRouter(prefix="/streams", tags=["streams"])


def get_stream_service(db: Session = Depends(get_db)):
    cctv_repository = CctvRepository(db)
    location_repository = LocationRepository(db)
    return StreamService(cctv_repository, location_repository)


@router.get("/cctv/{cctv_id}")
async def get_single_stream(
    cctv_id: int,
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
    """Get stream URLs untuk single CCTV"""
    stream_data = await service.get_stream_urls(cctv_id)
    return success_response(
        message=f"Stream URLs CCTV {cctv_id} berhasil ditampilkan",
        data=stream_data
    )


@router.get("/location/{location_id}")
async def get_location_streams(
    location_id: int,
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
    """Get semua streams untuk satu lokasi"""
    location_streams = await service.get_streams_by_location(location_id)
    return success_response(
        message=f"Streams lokasi {location_id} berhasil ditampilkan",
        data=location_streams
    )


@router.get("/location/{location_id}/events")
async def stream_location_events(
    location_id: int,
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
    """
    SSE endpoint untuk realtime updates
    Frontend: new EventSource('/streams/location/1/events')
    """
    return await service.stream_location_events(location_id)


@router.get("/mediamtx/status")
async def get_mediamtx_status(
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
    """Check status MediaMTX server"""
    is_online = await service.mediamtx_service.test_mediamtx_connection()
    return success_response(
        message="MediaMTX status",
        data={
            "status": "online" if is_online else "offline",
            "is_online": is_online
        }
    )


@router.get("/mediamtx/all-streams")
async def get_all_streams_status(
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
    """Get status semua streams yang terdaftar di MediaMTX"""
    all_status = await service.mediamtx_service.get_all_streams_status()
    
    streams_list = [
        {
            "stream_key": key,
            "status": info.status.value,
            "has_source": info.has_source,
            "source_ready": info.source_ready,
            "last_updated": info.last_updated.isoformat()
        }
        for key, info in all_status.items()
    ]
    
    return success_response(
        message="Status semua streams",
        data={
            "total_streams": len(streams_list),
            "streams": streams_list
        }
    )