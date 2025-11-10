from models.location_model import Location
from.base import Session, History, CctvCamera
from sqlalchemy import func
class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 50):
        return (
            self.db.query(
                History.id_history,
                History.id_cctv,
                History.note,
                History.status,
                History.service,
                func.to_char(func.timezone('Asia/Jakarta', History.created_at), 'YYYY-MM-DD HH24:MI:SS').label("created_at"),
                CctvCamera.titik_letak.label("cctv_name"),
                CctvCamera.ip_address.label("cctv_ip"),
                Location.nama_lokasi.label("location_name")
            )
            .join(CctvCamera, History.id_cctv == CctvCamera.id_cctv)
            .join(Location, CctvCamera.id_location == Location.id_location)
            .order_by(History.id_history.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_history(self, cctv_id: int,  service: bool = False) -> History:
            db_history = History(
                id_cctv=cctv_id,
                # note=note,
                service=service,
                status=False
            )
            self.db.add(db_history)
            self.db.commit()
            self.db.refresh(db_history)
            return db_history

    def create(self,  history: History):
       db_history = History(
           id_cctv = history.id_cctv,
           note = history.note,
           status = True
       )
       self.db.add(db_history)
       self.db.commit()
       self.db.refresh(db_history)
       return db_history

    def get_by_id(self, history_id: int):
       return self.db.query(History).filter(
           History.id_history == history_id
        ).first()

    def get_latest_by_cctv(self, cctv_id: int):
        return self.db.query(History).filter(
            History.id_cctv == cctv_id
        ).order_by(History.created_at.desc()).first()

    def get_by_cctv(self, cctv_id: int, limit: int = 50):
        return self.db.query(History).filter(
            History.id_cctv == cctv_id
        ).order_by(History.created_at.desc()).limit(limit).all()

   

    def update(self, history_id: int, history: History):
        db_history = self.get_by_id(history_id)
        if not db_history:
            return None
        if history.note:
            db_history.note = history.note
        if history.service:
            db_history.service = history.service
        self.db.commit()
        self.db.refresh(db_history)
        return db_history
        
    def update_service_status(self, history_id: int, service: bool) -> History:
        """Update service status untuk history tertentu"""
        db_history = self.get_by_id(history_id)
        if not db_history:
            return None
        db_history.service = service
        self.db.commit()
        self.db.refresh(db_history)
        return db_history
