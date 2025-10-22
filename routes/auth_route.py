from.base import APIRouter, Depends, Session, get_db
from services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=["auth"])

@router.post("/login")
def login(username: str, password: str, db: Session =Depends(get_db)):
    service = AuthService(db)
    return service.login(username, password)