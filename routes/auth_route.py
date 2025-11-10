from fastapi import HTTPException, status
from.base import APIRouter, Depends, Session, get_db
from services.auth_service import AuthService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from core.security import verify_token
from jose import JWTError
router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()
@router.post("/login")
def login(
    # form_data: OAuth2PasswordRequestForm = Depends()    
    username: str,
    password: str,
    db: Session =Depends(get_db)
):
    service = AuthService(db)
    result = service.login(username, password)
    
    return {    
        "access_token": result["access_token"],
        "refresh_token": result.get("refresh_token"),  # Opsional
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh(credentials: HTTPAuthorizationCredentials = Depends(security),
            db: Session = Depends(get_db)
):
    try:
        # Verifikasi refresh token
        payload = verify_token(credentials.credentials, token_type="refresh")
        
        # Generate access token baru
        service = AuthService(db)
        new_access_token = service.refresh_access_token(payload.get("sub"))
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    
@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    return service.logout(credentials.credentials)