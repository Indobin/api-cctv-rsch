from repositories.role_repository import RoleRepository
from schemas.role_schemas import RoleResponse, RoleCreate
from fastapi import HTTPException, status
class RoleService:
    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    def get_all_role(self, skip: int = 0, limit: int = 50 ):
        return self.role_repository.get_all(skip, limit)
    
    def create_role(self, role: RoleCreate):
        exiting_name = self.role_repository.get_by_name(role.nama_role)
        if exiting_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role sudah ada"
            )
        return self.role_repository.create(role)