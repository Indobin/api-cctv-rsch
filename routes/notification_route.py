from.base import APIRouter, Depends, Session, get_db, all_roles, success_response
from.base import NotificationRepository, HistoryRepository, CctvRepository, UserRepository
from services.notification_service import NotificationService
from schemas.notification_schemas import NotificationResponse
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notification", tags=["notifications"])

def get_notification_service(db: Session = Depends(get_db)):
    notification_repo = NotificationRepository(db)
    history_repo = HistoryRepository(db)
    cctv_repo = CctvRepository(db)
    user_repo = UserRepository(db)
    return NotificationService(notification_repo, history_repo, cctv_repo, user_repo)

@router.get("/")
def get_notifications(
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
    user_id = user_role.id_user
    notifications = service.get_user_notifications(user_id)
    response_data = [NotificationResponse.from_orm(loc) for loc in notifications]
    return success_response(
        message="Daftar notifikasi berhasil ditampilkan",
        data=response_data
    )

@router.get("/count")
def get_notification_count(
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
    user_id = user_role.id_user
    count = service.get_notification_count(user_id)
    
    return success_response(
        message="Jumlah notifikasi berhasil diambil",
        data={"count": count}
    )

@router.delete("/{notification_id}", response_model=dict)
def delete_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
    user_id = user_role.id_user
    deleted = service.delete_notification(notification_id, user_id)
    
    return success_response(
        message="Notifikasi berhasil dihapus",
        data={"deleted": deleted}
    )

@router.delete("/")
def delete_all_notifications(
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
  
    user_id = user_role.id_user
    deleted_count = service.delete_all_notifications(user_id)
    
    return success_response(
        message="Notifikasi berhasil dihapus",
        data={"deleted_count": deleted_count}
    )

#