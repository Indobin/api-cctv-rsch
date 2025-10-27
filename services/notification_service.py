from repositories.notification_repository import NotificationRepository
from repositories.history_repository import HistoryRepository
from repositories.cctv_repository import CctvRepository
from repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        history_repo: HistoryRepository,
        cctv_repo: CctvRepository,
        user_repo: UserRepository
    ):
        self.notification_repo = notification_repo
        self.history_repo = history_repo
        self.cctv_repo = cctv_repo
        self.user_repo = user_repo
        self.notification_tracker: Dict[str, Dict] = {}
   
    def _create_notification(self, cctv_id: int, note: str):
            """Create notification for all users"""
            try:
                user_ids = self.user_repo.get_all_id()
                
                # Create history entry
                history = self.history_repo.create_notif(cctv_id, note)
                
                # Create notification for each user
                notification_count = 0
                for user_id in user_ids:
                    self.notification_repo.create(user_id, history.id_history)
                    notification_count += 1
                
                logger.info(f"✅ Notification created for CCTV {cctv_id}: {note} (sent to {notification_count} users)")
                
                return {
                    "sent": True,
                    "history_id": history.id_history,
                    "user_count": notification_count
                }
            except Exception as e:
                logger.error(f"❌ Failed to create notification: {str(e)}")
                return {
                    "sent": False,
                    "error": str(e)
                }
        
    def _should_send_notification(self, stream_key: str, new_status: bool) -> bool:
        """Check if notification should be sent to avoid duplicates"""
        tracker = self.notification_tracker.get(stream_key, {})
        last_status = tracker.get("last_status")
        
        # Send notification if:
        # 1. No previous status recorded (first time)
        # 2. Status changed from previous state
        if last_status is None or last_status != new_status:
            return True
        
        logger.debug(f"Skipping duplicate notification for {stream_key} (status unchanged: {new_status})")
        return False
    
    # def handle_webhook_unpublish(self, stream_key: str, metadata: Optional[Dict] = None):
    #     """Handle stream disconnection event"""
    #     logger.info(f"🔴 Stream '{stream_key}' UNPUBLISH event received")
        
    #     # Find CCTV by stream key
    #     cctv = self.cctv_repo.get_by_stream_key(stream_key)
    #     if not cctv:
    #         logger.warning(f"⚠️ CCTV with stream_key '{stream_key}' not found in database")
    #         return {
    #             "success": False, 
    #             "message": "CCTV not found",
    #             "stream_key": stream_key
    #         }
        
    #     # Update streaming status in database
    #     self.cctv_repo.update_streaming_status(cctv.id_cctv, False)
    #     logger.info(f"📝 Updated CCTV {cctv.id_cctv} status to offline")
        
    #     # Check if notification should be sent
    #     if not self._should_send_notification(stream_key, False):
    #         return {
    #             "success": True,
    #             "duplicate": True,
    #             "message": "Notification already sent for this state"
    #         }
        
    #     # Create notification
    #     note = f"CCTV offline di titik '{cctv.titik_letak}'. Koneksi terputus."
    #     result = self._create_notification(cctv.id_cctv, note)
        
    #     # Update tracker
    #     self.notification_tracker[stream_key] = {
    #         "is_notified": True,
    #         "last_status": False,
    #         "cctv_id": cctv.id_cctv
    #     }
        
    #     return {
    #         "success": True,
    #         "status": "offline",
    #         "cctv_id": cctv.id_cctv,
    #         "cctv_name": cctv.titik_letak,
    #         "notification": result
    #     }
    
    # def handle_webhook_publish(self, stream_key: str, metadata: Optional[Dict] = None):
    #     """Handle stream connection event"""
    #     logger.info(f"🟢 Stream '{stream_key}' PUBLISH event received")
        
    #     # Find CCTV by stream key
    #     cctv = self.cctv_repo.get_by_stream_key(stream_key)
    #     if not cctv:
    #         logger.warning(f"⚠️ CCTV with stream_key '{stream_key}' not found in database")
    #         return {
    #             "success": False, 
    #             "message": "CCTV not found",
    #             "stream_key": stream_key
    #         }
        
    #     # Update streaming status in database
    #     self.cctv_repo.update_streaming_status(cctv.id_cctv, True)
    #     logger.info(f"📝 Updated CCTV {cctv.id_cctv} status to online")
        
    #     # Check if notification should be sent
    #     if not self._should_send_notification(stream_key, True):
    #         return {
    #             "success": True,
    #             "duplicate": True,
    #             "message": "Notification already sent for this state"
    #         }
        
    #     # Create notification
    #     note = f"CCTV kembali online di titik '{cctv.titik_letak}'. Streaming aktif."
    #     result = self._create_notification(cctv.id_cctv, note)
        
    #     # Update tracker
    #     self.notification_tracker[stream_key] = {
    #         "is_notified": True,
    #         "last_status": True,
    #         "cctv_id": cctv.id_cctv
    #     }
        
    #     return {
    #         "success": True,
    #         "status": "online",
    #         "cctv_id": cctv.id_cctv,
    #         "cctv_name": cctv.titik_letak,
    #         "notification": result
    #     }

    # def get_user_notifications(self, user_id: int) -> List[Dict]:
    #     notifications = self.notification_repo.get_by_user(user_id)
        
    #     notification = []
    #     for notif in notifications:
    #         history = notif.history
    #         cctv = history.cctv_camera if history else None
            
    #         notification.append({
    #             "notification_id": notif.id_notification,
    #             "history": {
    #                 "id": history.id_history,
    #                 "created_at": history.created_at.isoformat(),
    #                 "note": history.note,
    #                 "service": history.service,
    #             } if history else None,
    #             "cctv": {
    #                 "id": cctv.id_cctv,
    #                 "name": cctv.titik_letak,
    #                 "ip_address": cctv.ip_address,
    #                 "stream_key": cctv.stream_key,  
    #                 "is_streaming": cctv.is_streaming
    #             } if cctv else None
    #         })
        
    #     return notification

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete notifikasi (ketika user klik)"""
        notification = self.notification_repo.delete(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan id {user_id} tidak ditemukan"
            )
        return notification is not None

    def delete_all_notifications(self, user_id: int) -> int:
        """Delete semua notifikasi user"""
        return self.notification_repo.delete_all_by_user(user_id)

    def get_notification_count(self, user_id: int) -> int:
        return self.notification_repo.count_by_user(user_id)

    def mark_history_serviced(self, history_id: int, note: str = None) -> bool:
        notification = self.history_repo.mark_as_serviced(history_id, note)
        if notification:
            logger.info(f"History {history_id} marked as serviced")
        return notification is not None