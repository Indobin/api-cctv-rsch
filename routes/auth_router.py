from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=["auth"])

@router.post("/logn")
def login(username: str, password: str, db: Session =Depends(get_db)):
    service = AuthService(db)
    return service.login(username, password)