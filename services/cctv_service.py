from repositories.cctv_repository import CctvRepository
from repositories.location_repository import LocationRepository
from schemas.cctv_schemas import CctvCreate, CctvCreate1, CctvUpdate
from fastapi import HTTPException, status
from datetime import datetime
from io import BytesIO
import pandas as pd
import logging
from pydantic import ValidationError
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
                status_code=status.HTTP_404_NOT_FOUND,
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
        
        exiting_location = self.location_repository.get_by_name(cctv.nama_lokasi)
        if exiting_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lokasi sudah ada"
            )
        create_location = self.location_repository.create_by_analog(cctv.nama_lokasi)
        # stream_key = f"loc_{cctv.id_location}_analog"
        titik_analog = f"Analog {cctv.nama_lokasi}"
        cctv_data = {
            "titik_letak": titik_analog,
            "ip_address": cctv.ip_address,
            "id_location": create_location.id_location,
            "stream_key": None,
            "is_streaming": True
        }

        try:
            db_cctv = self.cctv_repository.create(cctv_data)
            db_cctv.cctv_location_name = cctv.nama_lokasi
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
        
    def export_cctvs(self):
        data = self.cctv_repository.get_all_for_export()
        df = pd.DataFrame([dict(row._mapping) for row in data])
        df.rename(columns={
            'titik_letak': 'Titik Letak',
            'ip_address': 'Ip Address',
            'cctv_location_name': 'Server Monitoring'
        }, inplace=True)

        unique_time = datetime.now().strftime("%Y%m%d%H%M%S") 

        output = BytesIO() 
        
        df.to_excel(output, index=False)
        
        output.seek(0)

        return {
            "data": output, 
            "filename": f"Cctvs_export_{unique_time}.xlsx",
            "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    
    @staticmethod
    def parse_import_cctv(uploaded_file):
        contents = uploaded_file.file.read()
        df = pd.read_excel(BytesIO(contents))
        
        rows = df.rename(columns={
            "Titik Letak": "titik_letak",
            "Ip Address": "ip_address",
            "Server Monitoring": "server_monitoring"
        }).to_dict('records')
        
        validated_rows = []
        errors = []
        
        for idx, row in enumerate(rows, start=2):  
            try:
                cctv = CctvCreate1(
                    titik_letak=row["titik_letak"],
                    ip_address=row["ip_address"],
                    nama_lokasi=row["server_monitoring"]
                )
                validated_rows.append(cctv.model_dump())
            except Exception as e:
                errors.append(f"Baris {idx}: {e.errors()[0]['msg']}")
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail={"message": "Data tidak valid", "errors": errors}
            )
            
        return validated_rows

        
    def import_cctvs(self, rows: list[dict]):
        ip_cek = {}
        titik_cek = {}

        for row in rows:
            ip = row["ip_address"]
            titik = row["titik_letak"]

            ip_cek[ip] = ip_cek.get(ip, 0) + 1
            titik_cek[titik] = titik_cek.get(titik, 0) +1
        
        internal_errors = []
        for ip, count in ip_cek.items():
            if count > 1:
                internal_errors.append(f"Duplikasi IP : {ip} muncul {count} kali.")
        for titik, count in titik_cek.items():
            if count > 1:
                internal_errors.append(f"Duplikasi Titik Letak : {titik} muncul {count} kali")

        if internal_errors:
            raise HTTPException(
                status_code=400,
               detail={
                    "message": "Data tidak valid: Terdapat duplikasi di dalam file yang diunggah.",
                    "errors": internal_errors
                }
            )
        create_cctvs = []
        update_cctvs = []

        server_names = list({row["nama_lokasi"] for row in rows})
        ip_list = [row["ip_address"] for row in rows]
        pos_list = [row["titik_letak"] for row in rows]

        existing_locations = self.location_repository.get_existing_locations(server_names)

        existing_cctvs = self.cctv_repository.get_existing_cctvs(ip_list, pos_list)
        by_ip = existing_cctvs["ip"]
        by_pos = existing_cctvs["position"]

        new_loc_names = [name for name in server_names if name not in existing_locations]

        if new_loc_names:
            new_locs = self.location_repository.bulk_create(new_loc_names)
            for loc in new_locs:
                existing_locations[loc.nama_lokasi] = loc

   
        for row in rows:

            location = existing_locations[row["nama_lokasi"]]

            existing = by_ip.get(row["ip_address"]) or by_pos.get(row["titik_letak"])

            cctv_data = {
                "titik_letak": row["titik_letak"],
                "ip_address": row["ip_address"],
                "id_location": location.id_location,
            }

            if existing:
               
                needs_update = (
                    existing.titik_letak != row["titik_letak"]
                    or existing.ip_address != row["ip_address"]
                    or existing.id_location != location.id_location
                )

                if needs_update:
                    update_cctvs.append((existing.id_cctv, cctv_data))

            else:
                if row["titik_letak"] in by_pos or row["ip_address"] in by_ip:
                    existing = by_pos.get(row["titik_letak"]) or by_ip.get(row["ip_address"])
                    update_cctvs.append((existing.id_cctv, cctv_data))
                    continue

                cctv_data["stream_key"] = (
                    f"loc_{location.id_location}_cam_{uuid.uuid4().hex[:8]}"
                )
                create_cctvs.append(cctv_data)

        imported = (
            self.cctv_repository.bulk_create(create_cctvs)
            if create_cctvs else []
        )

        updated = (
            self.cctv_repository.bulk_update(update_cctvs)
            if update_cctvs else []
        )

        return {
            "imported_cctvs": imported,
            "updated_cctvs": updated,
        }

