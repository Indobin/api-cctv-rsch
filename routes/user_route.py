from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from schemas.user_schemas import UserResponse, UserCreate, UserUpdate, UserDelete
from repositories.user_repository import UserRepository
from services.user_service import UserService
from core.auth import superadmin_role

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    return UserService(user_repo)

def success_response(message: str, data=None):
    return{
        "status": "success",
        "message": message,
        "data": data
    }

@router.get("/", response_model=dict)
def read_users(
    skip: int = 0,
    limit: int = 50,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    users = service.get_all_users(skip, limit)
    return success_response("Daftar pengguna berhasil ditampilkan", users)

@router.post("/", response_model=dict)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
    # user_role = Depends(superadmin_role)
):
    new_user = service.create_user(user)
    return success_response("User berhasil ditambahkan", UserResponse.from_orm(new_user))

@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    updated = service.update_user(user_id, user)
    return success_response("User berhasil diperbarui", UserResponse.from_orm(updated))

@router.delete("/soft/{user_id}", response_model=dict)
def soft_delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
): 
    deleted = service.soft_delete_user(user_id)
    return success_response("User berhasil di-soft delete", UserDelete.from_orm(deleted))

@router.delete("/hard/{user_id}", response_model=dict)
def hard_delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    deleted = service.hard_delete_user(user_id)
    return success_response("User berhasil di-hard delete", UserDelete.from_orm(deleted))

@router.get("/export")
def export_users(
    file_type: str = "xlsx",
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    file_path = service.export_users(file_type)
    return FileResponse(file_path, filename=f"users.{file_type}")

@router.post("/import")
def import_users(
    file: UploadFile = File(...),
    service: UserService = Depends(get_user_service),
    user_role = Depends(superadmin_role)
):
    rows = service.parse_import_user(file)
    imported = service.import_bulk(rows)
    return {
        "status": "success",
        "imported_count": len(imported),
    }