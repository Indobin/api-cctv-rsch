from.base import Session, History, CctvCamera

class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 50):
        return( self.db.query(
            History.id_history,
            CctvCamera.titik_letak.label("cctv_titik_letak"),
            History.note,
            History.created_at,
            History.service
        )
        .join(CctvCamera, History.id_cctv == CctvCamera.id_cctv)
        .offset(skip)
        .limit(limit)
        .all()
        )

    def create(self, cctv_id: int, history: History):
       db_history = History(
           id_cctv = cctv_id,
           note = history.note
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
        return history