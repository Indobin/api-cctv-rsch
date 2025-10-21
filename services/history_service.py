from repositories.history_repository import HistoryRepository
from repositories.cctv_repository import CctvRepository
from repositories.user_repository import UserRepository
from typing import List, Dict
from fastapi import HTTPException, status
import pandas as pd

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
        histories = self.history_repo.get_all(skip, limit)
        return histories