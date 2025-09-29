from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from schemas.cctv_schemas import CctvCreate, CctvUpdate, CctvResponse, StreamUrlsResponse
from fastapi import HTTPException, status, UploadFile
from services.mediamtx_service import MediaMTXService
import pandas as pd
import asyncio
import logging
from typing import Dict
import uuid
from pydantic import ValidationError
logger = logging.getLogger(__name__)

class CctvService:  
  
    def __init__(self, cctv_repository: CctvRepository, location_repository: LocationRepository):
        self.cctv_repository = cctv_repository
        self.location_repository= location_repository
        self.mediamtx_service = MediaMTXService()

    def get_all_cctv(self, skip: int = 0, limit: int = 50 ):
        users = self.cctv_repository.get_all(skip, limit)
        return [CctvResponse.from_orm(u) for u in users]
       
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
        stream_key = f"loc_{cctv.id_location}_cam_{uuid.uuid4().hex[:8]}"
        # Buat data CCTV tanpa setup stream dulu
        cctv_data = {
            "titik_letak": cctv.titik_letak,
            "ip_address": cctv.ip_address,
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
        
    def update_cctv(self, cctv_id: int, cctv: CctvUpdate):
        db_cctv = self.cctv_repository.get_by_id(cctv_id)
        if not db_cctv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Id cctv tidak ditemukan"
            )
        if cctv.ip_address:
            existing_ip = self.cctv_repository.get_by_ip(cctv.ip_address)
            if existing_ip and existing_ip.id_cctv != cctv_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="IP Address sudah ada"
                )
        if cctv.titik_letak:
            existing_position = self.cctv_repository.get_by_position(cctv.titik_letak)
            if existing_position and existing_position.id_cctv != cctv_id:
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
        stream_key = (
            f"loc_{cctv.id_location}_cam_{uuid.uuid4().hex[:8]}"
            if cctv.id_location is not None and cctv.id_location != db_cctv.id_location
            else db_cctv.stream_key
        )

        cctv_data = {
            "titik_letak": cctv.titik_letak if cctv.titik_letak is not None else db_cctv.titik_letak,
            "ip_address": cctv.ip_address if cctv.ip_address is not None else db_cctv.ip_address,
            "id_location": cctv.id_location if cctv.id_location is not None else db_cctv.id_location,
            "stream_key": stream_key,
            "is_streaming": db_cctv.is_streaming
        }

        db_cctv = self.cctv_repository.update(cctv_id,cctv_data)
        
        return CctvResponse.from_orm(db_cctv)

    def get_stream_urls(self, cctv_id: int) -> Dict:
        """Get stream URLs untuk CCTV"""
        cctv = self.cctv_repository.get_by_id(cctv_id)
        if not cctv:
            raise HTTPException(status_code=404, detail="CCTV tidak ditemukan")

        
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
    
    async def get_streams_by_location(self, location_id: int) -> Dict:
        existing_location = self.location_repository.get_by_id(location_id)
        if not existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lokasi tidak ditemukan"
            )
        cameras = self.cctv_repository.get_by_location(location_id).all()

         # Test MediaMTX connection sekali saja
        mediamtx_online = await self.mediamtx_service.test_mediamtx_connection()

          # Prepare response
        location_streams = {
            "location_id": location_id,
            "location_name": existing_location.nama_lokasi,
            "total_cameras": len(cameras),
            "mediamtx_status": "online" if mediamtx_online else "offline",
            "cameras": []
        }

        if not mediamtx_online:
            for cam in cameras:
                location_streams["cameras"].append({
                    "cctv_id": cam.id_cctv,
                    "titik_letak": cam.titik_letak,
                    "ip_address": cam.ip_address,
                    "stream_key": cam.stream_key,
                    "is_streaming": False,
                    "stream_urls": {}
                })
                return location_streams
        
        tasks = []
        for camera in cameras:
                # Bangun RTSP source URL untuk kamera ini
            rtsp_source_url = self.mediamtx_service.generate_rtsp_source_url(camera.ip_address)
             # Update status streaming di DB
            self.cctv_repository.update_streaming_status(camera.id_cctv, True)
            # Register stream ke MediaMTX
            tasks.append(
                self.mediamtx_service.ensure_stream(camera.stream_key, rtsp_source_url)
            )

        results = await asyncio.gather(*tasks)
        
              # isi response
        for cam, is_active in zip(cameras, results):
            stream_urls = self.mediamtx_service.generate_stream_urls(cam.stream_key)
            location_streams["cameras"].append({
                "cctv_id": cam.id_cctv,
                "titik_letak": cam.titik_letak,
                "ip_address": cam.ip_address,
                "stream_key": cam.stream_key,
                "is_streaming": is_active,
                "stream_urls": stream_urls if is_active else {}
            })
        return location_streams

    

        
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
        
    def export_cctv(self, file_type: str = "csv"):
        data = self.cctv_repository.get_all_for_export()
        df = pd.DataFrame([dict(row._mapping) for row in data])

        df.rename(columns={
            'titik_letak': 'Titik Letak',
            'ip_address': 'Ip Addres',
            'cctv_location_name': 'Server Monitoring'
        }, inplace=True)
        if file_type == "csv":
            file_path = "cctv_export.csv"
            df.to_csv(file_path, index=False, sep=';')
        else:
            file_path = "cctv_export.xlsx" # Pilih .xlsx
            df.to_excel(file_path, index=False)

        return file_path
    
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

