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
    user_id = user_role.get("user_id")
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

# @router.post("/notification/manual")
# async def test_create_notification(
#     cctv_id: int,
#     note: str = "Test notification - Manual trigger",
#     notification_service: NotificationService = Depends(get_notification_service)
# ):
#     """
#     Test endpoint untuk create notification
#     Example: POST /test/notification/manual?cctv_id=1&note=Test
#     """
#     logger.info(f"🧪 TEST: Manual notification test triggered for CCTV {cctv_id}")
    
#     result = await notification_service.create_notification(
#         cctv_id=cctv_id,
#         note=note
#     )
    
#     return {
#         "test": "manual_notification",
#         "result": result,
#         "timestamp": datetime.now().isoformat()
#     }
