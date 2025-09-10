from repositories.user_repository import UserRepository
from schemas.user_schemas import UserCreate, UserUpdate
from fastapi import HTTPException, status
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_all_users(self, skip: int = 0, limit: int = 50 ):
        return self.user_repository.get_all(skip, limit)
    
    def create_user(self, user: UserCreate):
        exiting_nip = self.user_repository.get_by_nip(user.nip)
        exiting_username = self.user_repository.get_by_username(user.username)
        if exiting_nip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nip sudah ada"
            )
        if exiting_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username sudah ada"
            )
        return self.user_repository.create(user)
    
    def update_user(self, user_id: int , user: UserUpdate):
        db_user = self.user_repository.get_by_id(user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Id user tidak ditemukan"
            )
        if user.nip:
            exiting_nip  = self.user_repository.get_by_nip(user.nip)
            if exiting_nip and exiting_nip.id_user != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nip sudah dipakai akun lain"
                )
        if user.username :
            exiting_username = self.user_repository.get_by_username(user.username)
            if exiting_username and exiting_username.id_user != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username sudah dipakai akun lain"
                )
        return self.user_repository.update(user_id, user)
        
    def hard_delete_user(self, user_id: int):
        user = self.user_repository.hard_delete(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {user_id} tidak ditemukan"
            )
        return {
            "message": f"User dengan id {user_id} berhasil dihapus"
        }

    def soft_delete_user(self, user_id: int):
        user = self.user_repository.soft_delete(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {user_id} tidak ditemukan"
            )
        return {"message": f"User dengan id {user_id} berhasil soft delete", "deleted_at": user.deleted_at}
        