from repositories.user_repository import UserRepository
from core.security import verify_password, create_access_token
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db):
        self.user_repository = UserRepository(db) 

    def login(self, username: str, password: str):
        user = self.user_repository.get_by_usernameL(username)
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah"
            )
        token = create_access_token({
            "sub": str(user.id_user),
            "id_role": user.id_role,
            "nama": user.nama
        })
        return {
            "access_token": token,
            "token_type": "bearer"
        }