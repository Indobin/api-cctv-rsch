from sqlalchemy import Null
from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from schemas.cctv_schemas import CctvCreate, CctvCreate1, CctvUpdate
from fastapi import HTTPException, status
import pandas as pd
import logging
# from typing import Dict
import uuid
logger = logging.getLogger(__name__)

class CctvService:  
  
    def __init__(self, cctv_repository: CctvRepository, location_repository: LocationRepository):
        self.cctv_repository = cctv_repository
        self.location_repository= location_repository

    def get_all_cctv(self, skip: int = 0, limit: int = 500 ):
        return self.cctv_repository.get_all(skip, limit)
       
    def create_cctv_ip(self, cctv: CctvCreate):
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
        
        # Generate stream key 
        stream_key = f"loc_{cctv.id_location}_cam_{uuid.uuid4().hex[:8]}"
       
        cctv_data = {
            "titik_letak": cctv.titik_letak,
            "ip_address": cctv.ip_address,
            "id_location": cctv.id_location,
            "stream_key": stream_key,
            "is_streaming": False
        }

        try:
            db_cctv = self.cctv_repository.create(cctv_data)
            db_location = self.location_repository.get_by_id(db_cctv.id_location)
            db_cctv.cctv_location_name = db_location.nama_lokasi
            return db_cctv
            
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saat membuat CCTV: {str(e)}"
            )
        
    def create_cctv_analog(self, cctv: CctvCreate1):
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
        stream_key = f"loc_{cctv.id_location}_analog"
        location_name = existing_location.nama_lokasi
        titik_analog = f"Analog {location_name}"
        cctv_data = {
            "titik_letak": titik_analog,
            "ip_address": cctv.ip_address,
            "id_location": cctv.id_location,
            "stream_key": None,
            "is_streaming": False
        }

        try:
            db_cctv = self.cctv_repository.create(cctv_data)
            db_cctv.cctv_location_name = location_name
            return db_cctv
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
        
        # Generate stream key 
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
        db_location = self.location_repository.get_by_id(db_cctv.id_location)
        db_cctv.cctv_location_name = db_location.nama_lokasi
        return db_cctv

    def soft_delete_cctv(self, cctv_id: int):
        cctv = self.cctv_repository.soft_delete(cctv_id)
        if not cctv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {cctv_id} tidak ditemukan"
            )
        return cctv
        
    def export_cctv(self, file_type: str = "csv"):
        data = self.cctv_repository.get_all_for_export()
        df = pd.DataFrame([dict(row._mapping) for row in data])

        df.rename(columns={
            'titik_letak': 'Titik Letak',
            'ip_address': 'Ip Address',
            'cctv_location_name': 'Server Monitoring'
        }, inplace=True)
        if file_type == "csv":
            file_path = "cctv_export.csv"
            df.to_csv(file_path, index=False, sep=';')
        else:
            file_path = "cctv_export.xlsx" 
            df.to_excel(file_path, index=False)

        return file_path
    
    @staticmethod
    def parse_import_cctv(uploaded_file):
        import pandas as pd
        from io import BytesIO

        contents = uploaded_file.file.read()
        df = pd.read_excel(BytesIO(contents))

        rows = []
        for _, row in df.iterrows():
            rows.append({
                "titik_letak": row.get("Titik Letak"),
                "ip_address": row.get("Ip Address"),
                "server_monitoring": row.get("Server Monitoring"),
            })
        return rows

    def import_bulk(self, rows: list[dict]):
      
        imported_cctvs = []

        for row in rows:
            lokasi = self.location_repository.get_by_name(row["server_monitoring"])
            if not lokasi:
                lokasi = self.location_repository.create(location=type("LocationCreate", (), {"nama_lokasi": row["server_monitoring"]}))
            existing = self.cctv_repository.get_by_ip(row["ip_address"])
            if existing:
                continue  

            stream_key = f"loc_{lokasi.id_location}_cam_{uuid.uuid4().hex[:8]}"
            cctv_data = {
                "titik_letak": row["titik_letak"],
                "ip_address": row["ip_address"],
                "stream_key": stream_key,
                "id_location": lokasi.id_location,
            }

            cctv = self.cctv_repository.create(cctv_data)
            imported_cctvs.append(cctv)

        return imported_cctvs