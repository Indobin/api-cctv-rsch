from repositories.user_repository import UserRepository
from schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from fastapi import HTTPException, status, UploadFile
import pandas as pd
class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_all_users(self, skip: int = 0, limit: int = 50 ):
        users = self.user_repository.get_all(skip, limit)
        return [UserResponse.from_orm(u) for u in users]
    
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
        return user

    def soft_delete_user(self, user_id: int):
        user = self.user_repository.soft_delete(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {user_id} tidak ditemukan"
            )
        return user
        
    def export_users(self, file_type: str = "csv"):
        data = self.user_repository.get_all_for_export()
        df = pd.DataFrame([dict(row._mapping) for row in data])

        if file_type == "csv":
            file_path = "users_export.csv"
            df.to_csv(file_path, index=False)
        else:
            file_path = "users_export.xlsx"
            df.to_excel(file_path, index=False)

        return file_path
    
    def import_users(self, file: UploadFile):
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif file.filename.endswith(".xlsx"):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="File harus CSV/XLSX")

        required_columns = {"nama", "nip", "username"}
        if not required_columns.issubset(set(df.columns)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Kolom wajib {required_columns} tidak lengkap di file",
            )

        # hapus row kosong
        df = df.dropna(subset=["nama", "nip", "username"])

        # konversi ke dict
        users = df.to_dict(orient="records")

            # validasi per-row
        clean_users = []
        for row in users:
            try:
                nama = str(row["nama"]).strip()
                nip = int(row["nip"]).strip()
                username = str(row["username"]).strip()
                password = str(row["password"]).strip() if "password" in row and row["password"] else None
                if not (nama and nip and username):
                    continue  # skip row kosong

                clean_users.append({
                    "nama": nama,
                    "nip": nip,
                    "username": username,
                    "password": password,
                })
            except Exception:
                continue  # skip row error

        results = self.user_repository.upsert_bulk(clean_users)

        return [UserResponse.from_orm(u) for u in results]

