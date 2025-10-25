from.base import APIRouter, Depends, Session, get_db, all_roles, success_response
from.base import HistoryRepository, CctvRepository, UserRepository
from schemas.history_schemas import HistoryResponse, HistoryCreate, HistoryUpdate
from services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])

def get_history_service(db: Session = Depends(get_db)):
    history_repo = HistoryRepository(db)
    cctv_repo = CctvRepository(db)
    user_repo = UserRepository(db)
    return HistoryService(history_repo, cctv_repo, user_repo)

@router.get("/")
def read_history(
    skip: int = 0,
    limit: int = 1000,
    service: HistoryService = Depends(get_history_service),
    user_role = Depends(all_roles)
):
    histories = service.get_all_hisotries(skip, limit)
    response_data = [HistoryResponse.from_orm(loc) for loc in histories]
    return success_response(
            message="Daftar semua history",
            data=response_data
    )
    
@router.post("/")
def create_history(
    history: HistoryCreate,
    service: HistoryService = Depends(get_history_service),
    user_role = Depends(all_roles)
):
    created = service.create_history(history)
    return success_response(
            message="History berhasil ditambahkan",
            data=HistoryResponse.from_orm(created)
    )
    
@router.put("/{history_id}")
def update_history(
    history_id: int,
    history: HistoryUpdate,
    service: HistoryService = Depends(get_history_service),
    user_role = Depends(all_roles)
):
    updated = service.update_history(history_id, history)
    return success_response(
            message="History berhasil diperbarui",
            data=HistoryResponse.from_orm(updated)
    )