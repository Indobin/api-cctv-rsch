from.base import APIRouter, Depends, Session, get_db, success_response, File, UploadFile
from repositories.user_repository import UserRepository
from repositories.role_repository import RoleRepository
from schemas.user_schemas import UserResponse, UserCreate, UserUpdate
from services.user_service import UserService
from core.auth import superadmin_role
from fastapi.responses import StreamingResponse
router = APIRouter(prefix="/users", tags=["users"])

def get_user_service(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    return UserService(user_repo, role_repo)

@router.get("/", response_model=dict)
def read_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    users = service.get_all_users(skip, limit)
    response_data = [UserResponse.from_orm(user) for user in users]
    return success_response(
        message="Daftar semua users", 
        data=response_data
    )

@router.post("/")
def create_user(
    user: UserCreate,
    # db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    new_user = service.create_user(user)
    return success_response(
        message="User berhasil ditambahkan", 
        data=UserResponse.from_orm(new_user)
    )

@router.put("/{user_id}")
def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    updated = service.update_user(user_id, user)
    return success_response(
        message="User berhasil diperbarui", 
        data=UserResponse.from_orm(updated)
    )

@router.delete("/soft/{user_id}")
def soft_delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
): 
    deleted = service.soft_delete_user(user_id)
    return success_response(
        message="User berhasil di-soft delete", 
        data=UserResponse.from_orm(deleted))

@router.delete("/hard/{user_id}")
def hard_delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    deleted = service.hard_delete_user(user_id)
    return success_response(
        message="User berhasil di-hard delete", 
        data=deleted
    )
@router.get("/export")
def export_users(
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    result = service.export_users()
    
    return StreamingResponse(
        content=result["data"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
        media_type=result["media_type"]
    )

@router.post("/import")
def import_users(
    file: UploadFile = File(...),
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    rows = service.parse_import_user(file)
    imported = service.import_users(rows)
    total_imported = len(imported.get("imported", []))
    total_updated = len(imported.get("updated", []))
    return success_response(
        message=f"Ditambahkan: {total_imported}, Diperbarui: {total_updated}",
        data={
            "total_imported": total_imported,
            "total_updated": total_updated,
        }
    )