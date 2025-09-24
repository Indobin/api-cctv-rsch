from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from schemas.cctv_schemas import CctvCreate, StreamUrlsResponse, SuccessResponse
from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from services.cctv_service import CctvService
from core.auth import get_superadmin
from core.response import success_response
import requests

router = APIRouter(prefix="/cctv", tags=["cctv"])


def get_cctv_service(db: Session = Depends(get_db)):
    cctv_repository = CctvRepository(db)
    location_repository = LocationRepository(db)
    return CctvService(cctv_repository, location_repository)

@router.get("/")
def read_cctv(
    skip: int = 0,
    limit: int = 50,
    service: CctvService = Depends(get_cctv_service),
    current_admin = Depends(get_superadmin)
):
    cctvs = service.get_all_cctv(skip, limit)
    return success_response(
            message="Cctv retrieved successfully",
            data=cctvs
        )


@router.post("/")
def create_cctv(
    cctv: CctvCreate,
    db: Session = Depends(get_db),
    service: CctvService = Depends(get_cctv_service),
    current_admin = Depends(get_superadmin)
):
    new_cctv = service.create_cctv(cctv)
    return success_response(
            message="Cctv retrieved successfully",
            data=new_cctv
        )

@router.get("/{cctv_id}/stream")
def get_cctv_stream(
    cctv_id: int,
    service: CctvService = Depends(get_cctv_service),
    current_admin = Depends(get_superadmin)
):
    stream_urls = service.get_stream_urls(cctv_id)
    return success_response(
        message="Stream URLs retrieved successfully",
        data=stream_urls
    )

@router.delete("/{cctv_id}")
def delete_cctv(
    cctv_id: int,
    service: CctvService = Depends(get_cctv_service),
    current_admin = Depends(get_superadmin)
):
    result = service.delete_cctv(cctv_id)
    return success_response(
        message=result["message"],
        data=None
    )

@router.get("/{cctv_id}/test")
def test_cctv_connection(
    cctv_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_superadmin),
    service: CctvService = Depends(get_cctv_service)
):
    test_result = service.test_cctv_connection(cctv_id)
    
    return success_response(
        message="Connection test completed",
        data=test_result
    )
