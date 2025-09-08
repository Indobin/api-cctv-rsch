from repositories.user_repository import UserRepository
from schemas.user_schemas import UserCreate, UserUpdate

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_all_users(self, skip: int = 0, limit: int = 50 ):
        return self.user_repository.get_all(skip, limit)
        