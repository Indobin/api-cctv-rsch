from repositories.history_repository import HistoryRepository
from repositories.cctv_repository import CctvRepository
from repositories.user_repository import UserRepository
from fastapi import HTTPException, status
import pandas as pd

from schemas.history_schemas import HistoryCreate, HistoryUpdate

class HistoryService:
    def __init__(
        self,
        history_repo: HistoryRepository,
        cctv_repo: CctvRepository,
        user_repo: UserRepository
    ):
        self.history_repo = history_repo
        self.cctv_repo = cctv_repo
        self.user_repo = user_repo

    def get_all_hisotries(self, skip: int = 0, limit: int = 1000):
        return self.history_repo.get_all(skip, limit)
        
    def create_history(self, history: HistoryCreate):
        existing_cctv = self.cctv_repo.get_by_id(history.id_cctv)
        if not existing_cctv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Id CCTV tidak ada"
            )
        db_history = self.history_repo.create(history)
        db_cctv = self.cctv_repo.get_by_id(db_history.id_cctv)
        db_history.cctv_name = db_cctv.titik_letak
        return db_history
        
    def update_history(self, history_id: int, history: HistoryUpdate):
        existing_history = self.history_repo.get_by_id(history_id)
        if not existing_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Id History tidak ada"
            )
        db_history = self.history_repo.update(history_id, history)
        db_cctv = self.cctv_repo.get_by_id(db_history.id_cctv)
        db_history.cctv_name = db_cctv.titik_letak
        return db_history
        
  