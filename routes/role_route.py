from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.role_schemas import Role, RoleBase, RoleCreate
from repositories.role_repository import RoleRepository
from services.role_service import RoleService
from core.auth import superadmin_role

router = APIRouter(prefix="/role", tags=["role"])

def get_role_service(db: Session = Depends(get_db)):
    role_repo = RoleRepository(db)
    return RoleService(role_repo)

@router.get("/", response_model=list[Role])
def read_role(
    skip: int = 0,
    limit: int = 50,
    service: RoleService = Depends(get_role_service),
    user_role = Depends(superadmin_role)
):
    return service.get_all_role(skip, limit)

@router.post("/", response_model=Role)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    service: RoleService = Depends(get_role_service),
    # user_role = Depends(superadmin_role)
):
    return service.create_role(role)

