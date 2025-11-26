from.base import APIRouter,File, Depends, UploadFile, Session, get_db, all_roles, superadmin_role, success_response
from.base import CctvRepository, LocationRepository
from fastapi.responses import FileResponse
from schemas.cctv_schemas import CctvCreate, CctvCreate1, CctvUpdate, CctvResponse
from services.cctv_service import CctvService
from fastapi.responses import StreamingResponse

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


@router.post("/ip")   
def create_cctv_ip(
    cctv: CctvCreate,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(superadmin_role)
):
    created = service.create_cctv_ip(cctv)
    return success_response(
        message="Cctv berhasil ditambahkan",
        data=CctvResponse.from_orm(created)
    )
@router.post("/analog")
def create_cctv_analog(
    cctv: CctvCreate1,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(superadmin_role)
):
    created = service.create_cctv_analog(cctv)
    return success_response(
        message="Cctv berhasil ditambahkan",
        data=CctvResponse.from_orm(created)
    )
@router.put("/{cctv_id}")
def update_cctv(
    cctv_id: int,
    cctv: CctvUpdate,
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(superadmin_role)
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
    user_role = Depends(superadmin_role)
):
    deleted = service.soft_delete_cctv(cctv_id)
    return success_response(
        message="Cctv berhasil dihapus", 
        data=deleted
    )

@router.get("/export")
def export_cctv(
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(superadmin_role)
):
    result = service.export_cctvs()
    
    return StreamingResponse(
       content=result["data"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        media_type=result["media_type"]
    )

@router.post("/import")
def import_cctv(
    file: UploadFile = File(...),
    service: CctvService = Depends(get_cctv_service),
    user_role = Depends(superadmin_role),
):
    rows = service.parse_import_cctv(file)
    result = service.import_cctvs(rows)

    total_imported = len(result.get("imported", []))
    total_updated = len(result.get("updated", []))
    
    message = (
        f"Data CCTV berhasil diproses. "
        f"Ditambahkan: {total_imported} data, "
        f"Diperbarui: {total_updated} data."
    )

    return success_response(
        message=message,
        data={
            "total_processed": len(rows),
            "total_imported": total_imported,
            "total_updated": total_updated,
        }
    )
        
