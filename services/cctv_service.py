from repositories.cctv_repository import CctvRepository
from schemas.cctv_schemas import CctvCreate, CctvUpdate, CctvResponse
from fastapi import HTTPException, status, UploadFile
import pandas as pd
class CctvService:

        
    RTSP_URL_TEMPLATE = "rtsp://admin:admin123@{ip_address}:554/cam/realmonitor?channel=1&subtype=0"

    def __init__(self, cctv_repository: CctvRepository):
        self.cctv_repository = cctv_repository

    def get_all_cctv(self, skip: int = 0, limit: int = 50 ):
        users = self.cctv_repository.get_all(skip, limit)
        return [CctvResponse.from_orm(u) for u in users]
    
    def create_cctv(self, cctv: CctvCreate):
        exiting_ip = self.cctv_repository.get_by_ip(cctv.ip_address)
        exiting_position = self.cctv_repository.get_by_position(cctv.titik_letak)
        if exiting_ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ip Address sudah ada"
            )
        if exiting_position:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Titik letak sudah ada"
            )
        rtsp_url_otomatis = self.RTSP_URL_TEMPLATE.format(ip_address=cctv.ip_address)
        cctv.ip_address = rtsp_url_otomatis
        return self.cctv_repository.create(cctv)
    
    # def update_user(self, user_id: int , cctv: UserUpdate):
    #     db_user = self.cctv_repository.get_by_id(user_id)
    #     if not db_user:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="Id cctv tidak ditemukan"
    #         )
    #     if cctv.nip:
    #         exiting_nip  = self.cctv_repository.get_by_nip(cctv.nip)
    #         if exiting_nip and exiting_nip.id_user != user_id:
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail="Nip sudah dipakai akun lain"
    #             )
    #     if cctv.username :
    #         exiting_position = self.cctv_repository.get_by_username(cctv.username)
    #         if exiting_position and exiting_position.id_user != user_id:
    #             raise HTTPException(
    #                 status_code=status.HTTP_400_BAD_REQUEST,
    #                 detail="Username sudah dipakai akun lain"
    #             )
    #     return self.cctv_repository.update(user_id, cctv)
        
    # def hard_delete_user(self, user_id: int):
    #     cctv = self.cctv_repository.hard_delete(user_id)
    #     if not cctv:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail=f"User dengan id {user_id} tidak ditemukan"
    #         )
    #     return cctv

    # def soft_delete_user(self, user_id: int):
    #     cctv = self.cctv_repository.soft_delete(user_id)
    #     if not cctv:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail=f"User dengan id {user_id} tidak ditemukan"
    #         )
    #     return cctv
        
    # def export_users(self, file_type: str = "csv"):
    #     data = self.cctv_repository.get_all_for_export()
    #     df = pd.DataFrame([dict(row._mapping) for row in data])

    #     if file_type == "csv":
    #         file_path = "users_export.csv"
    #         df.to_csv(file_path, index=False)
    #     else:
    #         file_path = "users_export.xlsx"
    #         df.to_excel(file_path, index=False)

    #     return file_path
    
    # def import_users(self, file: UploadFile):
    #     if file.filename.endswith(".csv"):
    #         df = pd.read_csv(file.file)
    #     elif file.filename.endswith(".xlsx"):
    #         df = pd.read_excel(file.file)
    #     else:
    #         raise HTTPException(status_code=400, detail="File harus CSV/XLSX")

    #     required_columns = {"nama", "nip", "username"}
    #     if not required_columns.issubset(set(df.columns)):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"Kolom wajib {required_columns} tidak lengkap di file",
    #         )

    #     # hapus row kosong
    #     df = df.dropna(subset=["nama", "nip", "username"])

    #     # konversi ke dict
    #     users = df.to_dict(orient="records")

    #         # validasi per-row
    #     clean_users = []
    #     for row in users:
    #         try:
    #             nama = str(row["nama"]).strip()
    #             nip = int(row["nip"]).strip()
    #             username = str(row["username"]).strip()
    #             password = str(row["password"]).strip() if "password" in row and row["password"] else None
    #             if not (nama and nip and username):
    #                 continue  # skip row kosong

    #             clean_users.append({
    #                 "nama": nama,
    #                 "nip": nip,
    #                 "username": username,
    #                 "password": password,
    #             })
    #         except Exception:
    #             continue  # skip row error

    #     results = self.cctv_repository.upsert_bulk(clean_users)

    #     return [UserResponse.from_orm(u) for u in results]

