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


    def should_send_notification(self, cctv_id: int) -> bool:
        latest_history = self.history_repo.get_latest_by_cctv(cctv_id)
        if latest_history is None:
            return True
        return latest_history.service == True

    def create_notification(
        
        self,
        cctv_id: int,
        user_ids: List[int],
        note: str = None
    ) -> Dict:
        """Membuat notifikasi baru"""
        if not self.should_send_notification(cctv_id):
            logger.info(f"CCTV {cctv_id} masih dalam perbaikan, skip notification")
            return {
                "sent": False,
                "reason": "CCTV masih dalam proses perbaikan"
            }

        history = self.history_repo.create(cctv_id, note)
        
        notifications = []
        for user_id in user_ids:
            notif = self.notification_repo.create(user_id, history.id_history)
            notifications.append(notif)

        cctv = self.cctv_repo.get_by_id(cctv_id)
        
        logger.info(
            f"created {len(notifications)} notifications: "
            f"CCTV {cctv_id} ({cctv.titik_letak if cctv else 'Unknown'}) is OFFLINE"
        )

        return {
            "sent": True,
            "history_id": history.id_history,
            "notification_count": len(notifications),
            "cctv_name": cctv.titik_letak if cctv else "Unknown"
        }

    
    def handle_webhook_disconnect(
        self,
        stream_key: str,
        metadata: Dict = None
    ) -> Dict:
        """Handler untuk MediaMTX webhook ketika stream disconnect"""
        logger.info(f"Webhook received: Stream '{stream_key}' DISCONNECTED")
        
        # Get CCTV by stream_key
        cctv = self.cctv_repo.get_by_stream_key(stream_key)
        if not cctv:
            logger.warning(f"CCTV dengan stream_key '{stream_key}' tidak ditemukan")
            return {"success": False, "message": "CCTV not found"}

        cctv_id = cctv.id_cctv
        
        # Update status streaming
        self.cctv_repo.update_streaming_status(cctv_id, False)
        
        # Check tracker untuk prevent duplicate
        tracker = self.notification_tracker.get(stream_key, {})
        if tracker.get("is_notified") and tracker.get("last_status") == False:
            logger.info(f"ℹNotification already sent for CCTV {cctv_id}, skipping")
            return {
                "success": True,
                "message": "Notification already sent",
                "duplicate": True
            }
        
        all_users = self.user_repo.get_all()  # Atau get_active_users()
        user_ids = [user.id_user for user in all_users]
        
        # Buat notifikasi
        note = f"Stream disconnected"
        if metadata:
            note += f" - {metadata}"
            
        result = self.create_notification(
            cctv_id=cctv_id,
            user_ids=user_ids,  
            note=note
        )
        
        # Update tracker
        if result["sent"]:
            self.notification_tracker[stream_key] = {
                "is_notified": True,
                "last_status": False
            }
        
        return {
            "success": True,
            "cctv_id": cctv_id,
            "cctv_name": cctv.titik_letak,
            "notification_sent": result["sent"],
            "user_count": len(user_ids),
            "reason": result.get("reason")
        }

    def handle_webhook_connect(
        self,
        stream_key: str,
        metadata: Dict = None
    ) -> Dict:
        """Handler untuk MediaMTX webhook ketika stream connect"""
        logger.info(f"Webhook received: Stream '{stream_key}' CONNECTED")
        
        # Get CCTV by stream_key
        cctv = self.cctv_repo.get_by_stream_key(stream_key)
        if not cctv:
            logger.warning(f"CCTV dengan stream_key '{stream_key}' tidak ditemukan")
            return {"success": False, "message": "CCTV not found"}

        cctv_id = cctv.id_cctv
        
        # Update status streaming di database
        self.cctv_repo.update_streaming_status(cctv_id, True)
        
        # Reset tracker
        self.notification_tracker[stream_key] = {
            "is_notified": False,
            "last_status": True
        }
        
        logger.info(f"CCTV {cctv_id} ({cctv.titik_letak}) is now ONLINE")
        
        return {
            "success": True,
            "cctv_id": cctv_id,
            "cctv_name": cctv.titik_letak,
            "status": "online"
        }

    def get_user_notifications(self, user_id: int) -> List[Dict]:
        notifications = self.notification_repo.get_by_user(user_id)
        
        notification = []
        for notif in notifications:
            history = notif.history
            cctv = history.cctv_camera if history else None
            
            notification.append({
                "notification_id": notif.id_notification,
                "history": {
                    "id": history.id_history,
                    "created_at": history.created_at.isoformat(),
                    "note": history.note,
                    "service": history.service,
                } if history else None,
                "cctv": {
                    "id": cctv.id_cctv,
                    "name": cctv.titik_letak,
                    "ip_address": cctv.ip_address,
                    "stream_key": cctv.stream_key,
                    "is_streaming": cctv.is_streaming
                } if cctv else None
            })
        
        return notification

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