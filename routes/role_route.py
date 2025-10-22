from.base import APIRouter, Depends, Session, get_db, success_response
from repositories.role_repository import RoleRepository
from schemas.role_schemas import RoleResponse, RoleCreate
from services.role_service import RoleService
from core.auth import superadmin_role

router = APIRouter(prefix="/role", tags=["role"])

def get_role_service(db: Session = Depends(get_db)):
    role_repo = RoleRepository(db)
    return RoleService(role_repo)

@router.get("/")
def read_role(
    skip: int = 0,
    limit: int = 50,
    service: RoleService = Depends(get_role_service),
    user_role = Depends(superadmin_role)
):
    roles = service.get_all_role(skip, limit)
    response_data = [RoleResponse.from_orm(role) for role in roles]
    return success_response(
        message="Daftar semua role",
        data=response_data
    )

@router.post("/")
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
    # user_role = Depends(superadmin_role)
):
    creted = service.create_role(role)
    return success_response(
        message="Role berhasil ditambahkan",
        data=RoleResponse.from_orm(creted)
    )

