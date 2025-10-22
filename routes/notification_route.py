from.base import APIRouter, Depends, Session, get_db, all_roles, success_response
from.base import NotificationRepository, HistoryRepository, CctvRepository, UserRepository
from services.notification_service import NotificationService
from schemas.notification_schemas import NotificationResponse, WebhookDisconnect, WebhookConnect


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
    
    return success_response(
        message="Daftar notifikasi berhasil ditampilkan",
        data=notifications
    )


@router.get("/count")
def get_notification_count(
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
    user_id = user_role.get("user_id")
    count = service.get_notification_count(user_id)
    
    return success_response(
        "Jumlah notifikasi berhasil diambil",
        data={"count": count}
    )

@router.delete("/{notification_id}", response_model=dict)
def delete_notification(
    notification_id: int,
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
    user_id = user_role.get("user_id")
    deleted = service.delete_notification(notification_id, user_id)
    
    return success_response(
        "Notifikasi berhasil dihapus",
        deleted
    )

@router.delete("/")
def delete_all_notifications(
    service: NotificationService = Depends(get_notification_service),
    user_role = Depends(all_roles)
):
  
    user_id = user_role.get("user_id")
    deleted_count = service.delete_all_notifications(user_id)
    
    return success_response(
        "Notifikasi berhasil dihapus",
        data={"deleted_count": deleted_count}
    )

@router.post("/stream-disconnect")
def webhook_disconnect(
    payload: WebhookDisconnect,
    service: NotificationService = Depends(get_notification_service)
):

    result = service.handle_webhook_disconnect(
        stream_key=payload.stream_key,
        metadata=payload.metadata
    )
    
    # if not result["success"]:
    #     raise HTTPException(status_code=404, detail=result["message"])
    
    return success_response(
        message="Webhook disconnect berhasil diproses",
        data=result
    )

@router.post("/stream-connect")
def webhook_connect(
    payload: WebhookConnect,
    service: NotificationService = Depends(get_notification_service)
):
   
    result = service.handle_webhook_connect(
        stream_key=payload.stream_key,
        metadata=payload.metadata
    )
    
    # if not result["success"]:
    #     raise HTTPException(status_code=404, detail=result["message"])
    
    return success_response(
        "Webhook connect berhasil diproses",
        data=result
    )