from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.user_schemas import UserResponse
from repositories.user_repository import UserRepository
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

def get_user_service(db: Session = Depends(get_db)):
    user_repository = UserRepository(db)
    return UserService(user_repository)

@router.get("/", response_model=list[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 50,
    service: UserService = Depends(get_user_service)
):
    return service.get_all_users(skip, limit)