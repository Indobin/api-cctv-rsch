from repositories.cctv_repository import CctvRepository
from schemas.cctv_schemas import CctvCreate, CctvUpdate, CctvResponse, StreamUrlsResponse
from fastapi import HTTPException, status, UploadFile
from services.mediamtx_service import MediaMTXService
import pandas as pd
import uuid
class CctvService:

        
    # RTSP_URL_TEMPLATE = "rtsp://admin:admin123@{ip_address}:554/cam/realmonitor?channel=1&subtype=0"

    def __init__(self, cctv_repository: CctvRepository):
        self.cctv_repository = cctv_repository
        self.mediamtxm_service = MediaMTXService()

    def get_all_cctv(self, skip: int = 0, limit: int = 50 ):
        cctvs = self.cctv_repository.get_all(skip, limit)
        result = []
        for cctv in cctvs:
            cctv_dict = dict(cctv._mapping)
            # Tambahkan URL stream
            if cctv_dict.get('stream_key'):
                cctv_dict['rtsp_url'] = f"rtsp://{self.mediamtxm_service.host}:{self.mediamtxm_service.rtsp_port}/{cctv_dict['stream_key']}"
                cctv_dict['hls_url'] = f"http://{self.mediamtxm_service.host}:{self.mediamtxm_service.http_port}/{cctv_dict['stream_key']}/index.m3u8"
            result.append(CctvResponse(**cctv_dict))
        return result
    
    def create_cctv(self, cctv: CctvCreate):
        exiting_ip = self.cctv_repository.get_by_ip(cctv.ip_address)
        if exiting_ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ip Address sudah ada"
            )
        exiting_position = self.cctv_repository.get_by_position(cctv.titik_letak)
        if exiting_position:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Titik letak sudah ada"
            )
        
        # Generate stream key
        stream_key = f"cctv_{uuid.uuid4().hex[:8]}"
        
        # Buat data CCTV
        cctv_data = {
            "titik_letak": cctv.titik_letak,
            "ip_address": cctv.ip_address,
            "status": cctv.status,
            "id_location": cctv.id_location,
            "stream_key": stream_key,
            "is_streaming": False
        }

        db_cctv = self.cctv_repository.create(cctv_data)

        # Setup stream di MediaMTX
    #     stream_urls = self.mediamtxm_service.setup_stream(db_cctv.id_cctv, cctv.ip_address)

    #     if stream_urls:
    #         self.cctv_repository.update(db_cctv,  {"stream_key": stream_urls["stream_key"]})

    #         # Tambahkan URL ke response
    #         response = CctvResponse.from_orm(db_cctv)
    #         response.rtsp_url = stream_urls["rtsp_url"]
    #         response.hls_url = stream_urls["hls_url"]
    #         return response
    #     else:
    #         # Jika gagal setup stream, hapus CCTV
    #         self.cctv_repository.db.delete(db_cctv)
    #         self.cctv_repository.db.commit()
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Gagal setup stream di media server"
    #         )
        
    # def get_stream_urls(self, cctv_id: int):
    #     cctv = self.cctv_repository.get_by_id(cctv_id)
    #     if not cctv:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="CCTV tidak ditemukan"
    #         )
        
    #     if not cctv.stream_key:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="CCTV belum dikonfigurasi untuk streaming"
    #         )
        
    #     # Periksa status stream
    #     is_streaming = self.mediamtxm_service.get_stream_status(cctv.stream_key)
    #     self.cctv_repository.update_streaming_status(cctv_id, is_streaming)

    #     return StreamUrlsResponse(
    #         cctv_id=cctv.id_cctv,
    #         stream_key=cctv.stream_key,
    #         rtsp_url=f"rtsp://{self.mediamtxm_service.host}:{self.mediamtxm_service.rtsp_port}/{cctv.stream_key}",
    #         hls_url=f"http://{self.mediamtxm_service.host}:{self.mediamtxm_service.http_port}/{cctv.stream_key}/index.m3u8",
    #         is_streaming=is_streaming
    #     )
    
    def delete_cctv(self, cctv_id: int):
        """Hapus CCTV dan streamnya"""
        cctv = self.cctv_repository.get_by_id(cctv_id)
        if not cctv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CCTV tidak ditemukan"
            )
        
        # Hapus stream dari MediaMTX jika ada
        if cctv.stream_key:
            self.mediamtx_service.remove_stream(cctv.stream_key)
        
        # Soft delete dari database
        self.cctv_repository.update(cctv, {"deleted_at": datetime.now()})
        
        return {"message": "CCTV berhasil dihapus"}

    def get_all_streams_status(self):
        """Dapatkan status semua stream"""
        streams = self.mediamtx_service.get_all_streams()
        return streams
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

