from.base import APIRouter,File, Depends, UploadFile, Session, get_db, all_roles, success_response
from.base import CctvRepository, LocationRepository
from fastapi.responses import FileResponse
from schemas.cctv_schemas import CctvCreate, CctvUpdate, CctvResponse
from services.cctv_service import CctvService

router = APIRouter(prefix="/cctv", tags=["cctv"])


def get_cctv_service(db: Session = Depends(get_db)):
    cctv_repo = CctvRepository(db)
    location_repo = LocationRepository(db)
    return CctvService(cctv_repo, location_repo)

@router.get("/")
def read_cctvs(
    skip: int = 0,
    limit: int = 500,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    cctvs = service.get_all_cctv(skip, limit)
    response_data = [CctvResponse.from_orm(loc) for loc in cctvs]
    return success_response(
        message="Daftar semua cctv",
        data=response_data
    )


@router.post("/")   
def create_cctv(
    cctv: CctvCreate,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    created = service.create_cctv(cctv)
    return success_response(
        message="Cctv berhasil ditambahkan",
        data=CctvResponse.from_orm(created)
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
        data=CctvResponse.from_orm(updated)
    )

@router.delete("/{cctv_id}")
def soft_delete_cctv(
    cctv_id: int,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(all_roles)
):
    deleted = service.soft_delete_cctv(cctv_id)
    return success_response(
        message="Cctv berhasil dihapus", 
        data=deleted
    )

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

    return success_response(
        message="Cctv berhasil diimport",
        data=len(imported)   
    )
   