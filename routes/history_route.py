from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.history_schemas import HistoryResponse, HistoryCreate, HistoryUpdate, HistoryDelete
from repositories.history_repository import HistoryRepository
from services.history_service import HistoryService
from core.auth import all_roles
from core.response import success_response

router = APIRouter(prefix="/history", tags=["history"])

def get_history_service(db: Session = Depends(get_db)):
    history_repo = HistoryRepository(db)
    return HistoryService(history_repo)

# @router.get("/")