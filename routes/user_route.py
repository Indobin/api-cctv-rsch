from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user_schemas import UserResponse, UserCreate, UserUpdate, UserDelete
from repositories.user_repository import UserRepository
from services.user_service import UserService
from core.auth import get_superadmin

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service(db: Session = Depends(get_db)):
    user_repository = UserRepository(db)
    return UserService(user_repository)

@router.get("/", response_model=list[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 50,
    service: UserService = Depends(get_user_service),
    current_admin = Depends(get_superadmin)
):
    return service.get_all_users(skip, limit)

@router.post("/create", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    service: UserService = Depends(get_user_service),
    current_admin = Depends(get_superadmin)
):
    return service.create_user(user)

@router.put("/update/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_admin = Depends(get_superadmin)
):
    return service.update_user(user_id, user)

@router.delete("/soft/{user_id}", response_model=UserDelete)
def soft_delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_admin = Depends(get_superadmin)
): 
    return service.soft_delete_user(user_id)

@router.delete("/hard/{user_id}", response_model=UserDelete)
def hard_delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_admin = Depends(get_superadmin)
):
    return service.hard_delete_user(user_id)