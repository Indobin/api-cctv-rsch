from repositories.notification_repository import NotificationRepository
from repositories.history_repository import HistoryRepository
from repositories.cctv_repository import CctvRepository
from repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import HTTPException, status
import logging
import asyncio
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
   
   
    async def create_notification(self, cctv_id: int):
        logger.info(f"🔵 ENTER create_notification: cctv_id={cctv_id}")
        latest_history = self.history_repo.get_latest_by_cctv(cctv_id)
        if latest_history is None or latest_history.service is True:
            try:
                
                logger.info(f"🔵 Step 1: Getting user IDs...")
                user_ids = await asyncio.to_thread(self.user_repo.get_all_id)
                logger.info(f"🟢 Step 1 DONE: Found {len(user_ids)} users: {user_ids}")
                
                logger.info(f"🔵 Step 2: Creating history...")
                history = await asyncio.to_thread(
                    self.history_repo.create_history,
                    cctv_id
                    # note
                )
                logger.info(f"🟢 Step 2 DONE: History ID={history.id_history}")
                
                logger.info(f"🔵 Step 3: Creating notifications...")
                notification_count = 0
                for user_id in user_ids:
                    logger.debug(f"   Creating notification for user {user_id}...")
                    await asyncio.to_thread(
                        self.notification_repo.create,
                        user_id, 
                        history.id_history
                    )
                    notification_count += 1
                    logger.debug(f"   ✓ Notification {notification_count} created")
                
                logger.info(f"🟢 Step 3 DONE: {notification_count} notifications created")
                logger.info(f"✅ SUCCESS: Notification flow completed for CCTV {cctv_id}")
                
                return {
                    "sent": True,
                    "history_id": history.id_history,
                    "user_count": notification_count
                }
                
            except Exception as e:
                logger.error(f"❌ EXCEPTION in create_notification: {type(e).__name__}: {str(e)}", exc_info=True)
                return {
                    "sent": False,
                    "error": str(e)
                }
        else:
            logger.info(f"⏭️ Notifikasi diabaikan untuk CCTV {cctv_id}. Sudah ada event OFFLINE terakhir yang belum diservis.")
            return {"sent": False, "reason": "Existing un-serviced offline event"}
   

    def get_user_notifications(self, user_id: int) -> List[Dict]:
        notifications = self.notification_repo.get_by_user(user_id)
        
        response_data = []
        for notif in notifications:
            history = notif.history
            cctv = history.cctv_camera if history and history.cctv_camera else None
            
            # Inisialisasi dictionary datar
            flat_data = {
                # Dari Notification
                "id_notification": notif.id_notification,
                
                # Dari History
                "id_history": history.id_history if history else None,
                "created_at": history.created_at if history else None,
                "note": history.note if history else None,
                
                # Dari CCTV
                "id_cctv": cctv.id_cctv if cctv else None,
                "titik_letak": cctv.titik_letak if cctv else None,
                "ip_address": cctv.ip_address if cctv else None,
            }
            
            response_data.append(flat_data)
            
        return response_data

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete notifikasi (ketika user klik)"""
        notification = self.notification_repo.delete(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notifikasi dengan id {notification_id} tidak ditemukan untuk user {user_id}."
            )
        return notification is not None

    def delete_all_notifications(self, user_id: int) -> int:
        """Delete semua notifikasi user"""
        return self.notification_repo.delete_all_by_user(user_id)

    def get_notification_count(self, user_id: int) -> int:
        return self.notification_repo.count_by_user(user_id)
