from.base import Session, CctvCamera, Location
from sqlalchemy import Null, func
from datetime import datetime
from zoneinfo import ZoneInfo

class CctvRepository:
    def __init__(self, db:Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 50):
        return(
            self.db.query(
                CctvCamera.id_cctv,
                CctvCamera.titik_letak,
                CctvCamera.ip_address,
                CctvCamera.is_streaming,
                CctvCamera.id_location,
                CctvCamera.stream_key,
                Location.nama_lokasi.label("cctv_location_name"),  
                func.to_char(func.timezone('Asia/Jakarta', CctvCamera.created_at), 'YYYY-MM-DD HH24:MI:SS').label("created_at"),
                func.to_char(func.timezone('Asia/Jakarta', CctvCamera.updated_at), 'YYYY-MM-DD HH24:MI:SS').label("updated_at"),
                func.to_char(func.timezone('Asia/Jakarta', CctvCamera.deleted_at), 'YYYY-MM-DD HH24:MI:SS').label("deleted_at"),
            )
            .join(Location, CctvCamera.id_location == Location.id_location)
            .where(CctvCamera.deleted_at == None)
            .order_by(CctvCamera.id_cctv.desc())
            .offset(skip)
            .limit(limit)
            .all()
    )
    
    def get_all_stream(self, skip: int = 0, limit: int = 50):
        return(
            self.db.query(
                CctvCamera.id_cctv,
                CctvCamera.titik_letak,
                CctvCamera.ip_address,
                CctvCamera.is_streaming,
                CctvCamera.stream_key,
            )
            .where(CctvCamera.deleted_at == None, ~(CctvCamera.titik_letak.startswith("Analog")))
            .order_by(CctvCamera.id_cctv.desc())
            .offset(skip)
            .limit(limit)
            .all()
    )
    
    def get_by_position(self, titik_letak: str):
        return self.db.query(CctvCamera).filter(CctvCamera.titik_letak == titik_letak).where(CctvCamera.deleted_at == None).first()
    
    def get_by_ip(self, ip_address: str):
        return self.db.query(CctvCamera).filter(CctvCamera.ip_address == ip_address).where(CctvCamera.deleted_at == None).first()

    def get_by_id(self, id_cctv: int):
        return self.db.query(CctvCamera).filter(CctvCamera.id_cctv == id_cctv).first()
    
    def get_by_stream_key(self, stream_key: str):
        return self.db.query(CctvCamera).filter(CctvCamera.stream_key == stream_key).first()

    def get_by_location(self, id_location: int):
        return self.db.query(CctvCamera).filter(CctvCamera.id_location == id_location).where(CctvCamera.deleted_at == None)

    def create(self, cctv_data: dict):
        db_cctv = CctvCamera(**cctv_data)
        self.db.add(db_cctv)
        self.db.commit()
        self.db.refresh(db_cctv)
        return db_cctv
    
    def update(self, cctv_id: int, update_data: dict):
        db_cctv = self.get_by_id(cctv_id)
        if not db_cctv:
            return None
        for field, value in update_data.items():
            setattr(db_cctv, field, value)
        self.db.commit()
        self.db.refresh(db_cctv)
        return db_cctv

    def update_streaming_status(self, cctv_id: int, is_streaming: bool):
        cctv = self.get_by_id(cctv_id)
        if cctv:
            cctv.is_streaming = is_streaming
            self.db.commit()
            self.db.refresh(cctv)
        return cctv
    
    def soft_delete(self, cctv_id:int):
        db_cctv = self.get_by_id(cctv_id)
        if not db_cctv:
            return None
        utc_now = datetime.now(ZoneInfo("UTC"))
        db_cctv.deleted_at = utc_now
        self.db.commit()
        self.db.refresh(db_cctv)
        return db_cctv
    
    
    def get_all_for_export(self):
        return (
            self.db.query(
                CctvCamera.titik_letak,
                CctvCamera.ip_address,
                Location.nama_lokasi.label("cctv_location_name"),  
            )
            .join(Location, CctvCamera.id_location == Location.id_location)
            .where(CctvCamera.deleted_at == None)
            .all()
    )

    def get_existing_ip(self, ip_address: list[str]):
       result = self.db.query(CctvCamera.ip_address)\
           .filter(CctvCamera.ip_address.in_(ip_address))\
           .where(CctvCamera.deleted_at == None)\
           .all()
       return {i[0] for i in result}
    
    def get_existing_position(self, titik_letak: list[str]):
       result = self.db.query(CctvCamera.titik_letak)\
           .filter(CctvCamera.titik_letak.in_(titik_letak))\
           .where(CctvCamera.deleted_at == None)\
           .all()
       return {t[0] for t in result}
    
    def bulk_create(self, cctv_data_list: list[dict]):
        db_cctvs = [CctvCamera(**data) for data in cctv_data_list]
        self.db.add_all(db_cctvs)
        self.db.commit()
        return db_cctvs

    def bulk_update(self, updates: list[tuple[int, dict]]):
        updated_cctvs = []
        for cctv_id, update_data in updates:
            db_cctv = self.get_by_id(cctv_id)
            if db_cctv:
                for field, value in update_data.items():
                    setattr(db_cctv, field, value)
                updated_cctvs.append(db_cctv)
        self.db.commit()
        return updated_cctvs

        