from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from schemas.cctv_schemas import CctvCreate, CctvUpdate, CctvResponse, StreamUrlsResponse
from fastapi import HTTPException, status, UploadFile
from services.mediamtx_service import MediaMTXService
import pandas as pd
import logging
from typing import Dict
import uuid
from typing import Dict
logger = logging.getLogger(__name__)

class CctvService:  
  
    def __init__(self, cctv_repository: CctvRepository, location_repository: LocationRepository):
        self.cctv_repository = cctv_repository
        self.location_repository= location_repository
        self.mediamtx_service = MediaMTXService()
    
    def create_cctv(self, cctv: CctvCreate):
        existing_ip = self.cctv_repository.get_by_ip(cctv.ip_address)
        if existing_ip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IP Address sudah ada"
            )
        
        existing_position = self.cctv_repository.get_by_position(cctv.titik_letak)
        if existing_position:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Titik letak sudah ada"
            )
        
        existing_location = self.location_repository.get_by_id(cctv.id_location)
        if not existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lokasi tidak ditemukan"
            )
        
        # Generate stream key untuk digunakan nanti
        # stream_key = f"cctv_{uuid.uuid4().hex[:8]}"
        stream_key = f"loc_{cctv.id_location}_cam_{uuid.uuid4().hex[:8]}"
        # Buat data CCTV tanpa setup stream dulu
        cctv_data = {
            "titik_letak": cctv.titik_letak,
            "ip_address": cctv.ip_address,
            "status": cctv.status,
            "id_location": cctv.id_location,
            "stream_key": stream_key,
            "is_streaming": False
        }

        try:
            # Buat record CCTV saja
            db_cctv = self.cctv_repository.create(cctv_data)
            
            # Return response tanpa URL stream (karena belum disetup)
            return CctvResponse.from_orm(db_cctv)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saat membuat CCTV: {str(e)}"
            )
        
    def get_stream_urls(self, cctv_id: int) -> Dict:
        """Get stream URLs untuk CCTV"""
        cctv = self.cctv_repository.get_by_id(cctv_id)
        if not cctv:
            raise HTTPException(status_code=404, detail="CCTV tidak ditemukan")
        
        # # Generate stream key jika belum ada
        # if not cctv.stream_key:
        #     stream_key = f"loc_{cctv.id_location}_cam_{uuid.uuid4().hex[:8]}"
        #     # self.cctv_repository.update_stream_key(cctv_id, stream_key)
        #     cctv.stream_key = stream_key
        #     self.db.commit()
        
        # Test MediaMTX connection
        mediamtx_online = self.mediamtx_service.test_mediamtx_connection()
        
        if mediamtx_online:
            rtsp_source_url = self.mediamtx_service.generate_rtsp_source_url(cctv.ip_address)
            stream_registered = self.mediamtx_service.add_stream_to_mediamtx(
                cctv.stream_key,
                rtsp_source_url
            )
            streaming_active = stream_registered
        else:
            streaming_active = False

        # Update status
        self.cctv_repository.update_streaming_status(cctv_id, streaming_active)

        # Generate URLs
        stream_urls = self.mediamtx_service.generate_stream_urls(cctv.stream_key)
        
        return {
            "cctv_id": cctv.id_cctv,
            "stream_key": cctv.stream_key,
            "stream_urls": stream_urls,
            "is_streaming": mediamtx_online,
            "mediamtx_status": "online" if mediamtx_online else "offline",
            "note": "Stream akan aktif ketika diakses pertama kali" if not mediamtx_online else "Stream ready"
        }
    
    def test_cctv_connection(self, cctv_id: int) -> Dict:
        """Test koneksi ke CCTV"""
        cctv = self.cctv_repository.get_by_id(cctv_id)
        if not cctv:
            raise HTTPException(status_code=404, detail="CCTV tidak ditemukan")
        
         # Generate RTSP URL untuk test
        rtsp_url = self.mediamtx_service.generate_rtsp_source_url(cctv.ip_address)
        
        # Simple reachability test (ping IP)
        try:
            import os
            import platform
            
            # Ping the IP address
            param = "-n" if platform.system().lower() == "windows" else "-c"
            response = os.system(f"ping {param} 1 {cctv.ip_address} > nul 2>&1")
            reachable = (response == 0)
        except:
            reachable = False
        
        return {
            "cctv_id": cctv.id_cctv,
            "ip_address": cctv.ip_address,
            "reachable": reachable,
            "rtsp_url": rtsp_url,
            "connection_status": "online" if reachable else "offline"
        }

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

