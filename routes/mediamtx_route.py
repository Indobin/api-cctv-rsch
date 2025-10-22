from.base import APIRouter, Depends, Session, get_db, all_roles, success_response
from.base import CctvRepository, LocationRepository
from services.mediamtx_service import MediaMTXService, StreamService

router = APIRouter(prefix="/streams", tags=["streams"])


def get_stream_service(db: Session = Depends(get_db)):
    cctv_repos = CctvRepository(db)
    location_repo = LocationRepository(db)
    return StreamService(cctv_repos, location_repo)


@router.get("/cctv/{cctv_id}")
async def get_single_stream(
    cctv_id: int,
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
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
    location_streams = await service.get_streams_by_location(location_id)
    return success_response(
        message=f"Streams lokasi {location_id} berhasil ditampilkan",
        data=location_streams
    )


@router.get("/mediamtx/status")
async def get_mediamtx_status(
    service: StreamService = Depends(get_stream_service),
    user_role = Depends(all_roles)
):
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