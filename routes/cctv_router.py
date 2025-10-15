from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from schemas.cctv_schemas import CctvCreate, CctvUpdate, CctvDelete, SuccessResponse
from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from services.cctv_service import CctvService
from core.auth import all_roles
from core.response import success_response
from fastapi.responses import FileResponse

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
    user_role = Depends(all_roles)
):
    cctvs = service.get_all_cctv(skip, limit)
    return success_response(
            message="Daftar cctv berhasil ditampilkan",
            data=cctvs
        )


@router.post("/")
def create_cctv(
    cctv: CctvCreate,
    db: Session = Depends(get_db),
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    new_cctv = service.create_cctv(cctv)
    return success_response(
            message="Cctv berhasil ditambahkan",
            data=new_cctv
        )

@router.put("/{cctv_id}")
def update_cctv(
    cctv_id: int,
    cctv: CctvUpdate,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    updated = service.update_cctv(cctv_id, cctv)
    return success_response(
        message="Cctv berhasil diperbarui",
        data=updated
    )

@router.delete("/{cctv_id}")
def soft_delete_cctv(
    cctv_id: int,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    deleted = service.soft_delete_cctv(cctv_id)
    return success_response("Lokasi berhasil dihapus", CctvDelete.from_orm(deleted))

@router.get("/export")
def export_cctv(
    file_type: str = "xlsx",
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    file_path = service.export_cctv(file_type)
    return FileResponse(file_path, filename=f"cctv.{file_type}")

@router.post("/import")
def import_cctv(
    file: UploadFile = File(...),
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles),
):
    
    # parsing Excel
    rows = service.parse_import_cctv(file)

    # import ke DB
    imported = service.import_bulk(rows)

    return {
        "status": "success",
        "imported_count": len(imported),
    }
