from models.user_model import User
from repositories.user_repository import UserRepository
from repositories.role_repository import RoleRepository
from schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from fastapi import HTTPException, status
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from core.security import hash_password  
from datetime import datetime
import pandas as pd

class UserService:
    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository):
        self.user_repository = user_repository
        self.role_repository = role_repository

    def get_all_users(self, skip: int = 0, limit: int = 50 ):
        return self.user_repository.get_all(skip, limit)

    def create_user(self, user: UserCreate):
        existing_nik = self.user_repository.get_by_nik(user.nik)
        existing_username = self.user_repository.get_by_username(user.username)
        existing_role = self.role_repository.get_by_id(user.id_role)
        if existing_nik:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nik sudah ada"
            )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username sudah ada"
            )
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role tidak ditemukan"
            )
        return self.user_repository.create(user)

    def update_user(self, user_id: int , user: UserUpdate):
        db_user = self.user_repository.get_by_id(user_id)
        existing_role = self.role_repository.get_by_id(user.id_role)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Id user tidak ditemukan"
            )
        if user.nik:
            existing_nik  = self.user_repository.get_by_nik(user.nik)
            if existing_nik and existing_nik.id_user != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nip sudah dipakai akun lain"
                )
        if user.username :
            existing_username = self.user_repository.get_by_username(user.username)
            if existing_username and existing_username.id_user != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username sudah dipakai akun lain"
                )
        if user.id_role:
            if not existing_role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Role tidak ditemukan"
                )
        return self.user_repository.update(user_id, user)

    def hard_delete_user(self, user_id: int):
        user = self.user_repository.hard_delete(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {user_id} tidak ditemukan"
            )
        return user

    def soft_delete_user(self, user_id: int):
        user = self.user_repository.soft_delete(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {user_id} tidak ditemukan"
            )
        return user

    def export_users(self):
        data = self.user_repository.get_all_for_export()
        df = pd.DataFrame([dict(row._mapping) for row in data])
        df.rename(columns={
                "nama": "Nama",
                "username": "Username",
                "nik": "Nik",
                "role": "Role"
            }, inplace=True)
            
        unique_time = datetime.now().strftime("%Y%m%d%H%M%S") 
        
        output = BytesIO() 
        
        df.to_excel(output, index=False)
        
        output.seek(0)

        return {
            "data": output, 
            "filename": f"Users_export_{unique_time}.xlsx",
            "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }

    @staticmethod
    def parse_import_user(uploaded_file):
        contents = uploaded_file.file.read()
        df = pd.read_excel(BytesIO(contents), dtype={'Nik': str})
        
        rows = df.rename(columns={
            "Nama": "nama",
            "Username": "username", 
            "Nik": "nik",
            "Password": "password",
            "Role": "role"
        }).to_dict('records')
        return rows

    # service
    def import_users(self, rows: list[dict]):
        imported_users = []
        DEFAULT_PASSWORD = "Rsch123"
        
        usernames = [row["username"] for row in rows]
        niks = [str(row["nik"]) for row in rows]
        
        existing_usernames = self.user_repository.get_existing_usernames(usernames)
        existing_niks = self.user_repository.get_existing_niks(niks)
        
        users_to_create = []
        
        for row in rows:
            nik_str = str(row["nik"])
            
            if row["username"] in existing_usernames or nik_str in existing_niks:
                continue
            
            password_value = row.get("password")
            if not password_value or len(str(password_value)) < 6:
                final_password = DEFAULT_PASSWORD
            else:
                final_password = str(password_value)
                
            role_str = row.get("role", "").lower()
            if role_str == "superadmin":
                id_role = 1
            else:
                id_role = 2
    
            users_to_create.append({
                "nama": row["nama"],
                "username": row["username"],
                "nik": nik_str,
                "password": final_password,
                "id_role": id_role 
            })
        
        if not users_to_create:
            return []
        
        passwords = [u["password"] for u in users_to_create]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            hashed_passwords = list(executor.map(hash_password, passwords))
        
        db_users = []
        for user_data, hashed_pwd in zip(users_to_create, hashed_passwords):
            db_user = User(
                nama=user_data["nama"],
                nik=user_data["nik"],
                username=user_data["username"],
                password=hashed_pwd,
                id_role=user_data["id_role"]
            )
            db_users.append(db_user)
        
        return self.user_repository.bulk_create(db_users)
        # return db_users

    
