from repositories.user_repository import UserRepository
from core.security import verify_password, create_access_token, create_refresh_token
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, db):
        self.user_repository = UserRepository(db) 

    def login(self, username: str, password: str):
        user = self.user_repository.get_by_usernameL(username)
        if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Username atau password salah"
                    )
                
        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah"
            )
        user_data = {
            "sub": str(user.id_user),
            "id_role": user.id_role,
            "nama": user.nama
        }
        update_last_login = self.user_repository.last_login(user.id_user)
        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id_user,
                "username": user.username,
                "role": user.id_role
            }
        }
    
    def refresh_access_token(self, user_id: str):
            user = self.user_repository.get_by_id(int(user_id))
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Buat access token baru
            user_data = {
                "sub": str(user.id_user),
                "nama": user.nama,
                "role": user.id_role
            }
            
            return create_access_token(user_data)
    def logout(self, token: str):
            
            return {"message": "Logout successful"}