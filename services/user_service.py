from models.user_model import User
from repositories.user_repository import UserRepository
from repositories.role_repository import RoleRepository
from schemas.user_schemas import UserCreate, UserUpdate
from fastapi import HTTPException, status
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from core.security import hash_password  
from datetime import datetime
from pydantic import ValidationError
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
        df = pd.read_excel(BytesIO(contents), dtype={"Nik": str})
        df.columns = df.columns.str.strip().str.lower()

        df = df.rename(columns={
            "nama": "nama",
            "username": "username",
            "nik": "nik",
            "password": "password",
            "role": "role"
        })
    
        rows = df.to_dict("records")
    
        validated_rows = []
        errors = []
    
        for idx, row in enumerate(rows, start=2):  
            try:
                role_str = str(row.get("role", "")).strip().lower()
                if not role_str:
                    raise ValueError("Role kosong")
    
                if role_str == "superadmin":
                    id_role = 1
                elif role_str == "security":
                    id_role = 2
                else:
                    raise ValueError(f"Role invalid: {role_str}")
 
                user = UserCreate(
                    nama=row.get("nama"),
                    username=row.get("username"),
                    nik=row.get("nik"),
                    password=row.get("password") or "Rsch123",  
                    id_role=id_role
                )
    
                validated_rows.append(user.model_dump())
    
            except Exception as e:
                errors.append(f"Baris {idx}: {e}")
    
        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Data tidak valid",
                    "errors": errors
                }
            )
    
        return validated_rows


    def import_users(self, rows: list[dict]):
   
       DEFAULT_PASSWORD = "Rsch123"
   
       usernames = [row["username"] for row in rows]
       niks = [str(row["nik"]) for row in rows]

       existing_users = self.user_repository.get_existing_users_by_username_or_nik(usernames, niks)
       users_by_username = {u.username: u for u in existing_users}
       users_by_nik = {u.nik: u for u in existing_users}
   
       users_to_create = []
       users_to_update = []
       passwords_to_hash = []
   
       for row in rows:
           nik_str = str(row["nik"])
           username = row["username"]
           id_role = row["id_role"]
           raw_password = row.get("password")
           if raw_password and len(str(raw_password)) >= 6:
               final_password = str(raw_password)
           else:
               final_password = DEFAULT_PASSWORD

           user_by_username = users_by_username.get(username)
           user_by_nik = users_by_nik.get(nik_str)
   
           if user_by_username and user_by_nik and user_by_username.id_user == user_by_nik.id_user:
               users_to_update.append({
                   "user": user_by_username,
                   "data": {
                       "nama": row["nama"],
                       "id_role": id_role,
                       "password": final_password
                   }
               })
               passwords_to_hash.append(final_password)

           elif user_by_username:
               users_to_update.append({
                   "user": user_by_username,
                   "data": {
                       "nik": nik_str,
                       "nama": row["nama"],
                       "id_role": id_role,
                       "password": final_password
                   }
               })
               passwords_to_hash.append(final_password)

           elif user_by_nik:
               users_to_update.append({
                   "user": user_by_nik,
                   "data": {
                       "username": username,
                       "nama": row["nama"],
                       "id_role": id_role,
                       "password": final_password
                   }
               })
               passwords_to_hash.append(final_password)

           else:
               users_to_create.append({
                   "nama": row["nama"],
                   "username": username,
                   "nik": nik_str,
                   "id_role": id_role,
                   "password": final_password
               })
               passwords_to_hash.append(final_password)

       if not passwords_to_hash:
           return {"imported": [], "updated": []}
  
       with ThreadPoolExecutor(max_workers=4) as executor:
           hashed_passwords = list(executor.map(hash_password, passwords_to_hash))
   
       hash_idx = 0
   
       for update_item in users_to_update:
           update_item["data"]["password"] = hashed_passwords[hash_idx]
           hash_idx += 1
   
       for user_data in users_to_create:
           user_data["password"] = hashed_passwords[hash_idx]
           hash_idx += 1
   
       updated_users = []
       for update_item in users_to_update:
           user = update_item["user"]
           for field, value in update_item["data"].items():
               setattr(user, field, value)
           updated_users.append(user)

       db_users = [User(**user_data) for user_data in users_to_create]
       self.user_repository.db.add_all(db_users)
   
       self.user_repository.db.commit()
   
       return {
           "imported": db_users,
           "updated": updated_users
       }


    