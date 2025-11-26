import asyncio
import logging
from typing import Callable, Optional

from repositories.cctv_repository import CctvRepository
from repositories.history_repository import HistoryRepository
from repositories.user_repository import UserRepository
from repositories.notification_repository import NotificationRepository
from services.notification_service import NotificationService
from services.mediamtx_service import MediaMTXService

logger = logging.getLogger(__name__)


class BackgroundCCTVMonitor:
    
    def __init__(
        self,
        check_interval: int = 40,
        db_session_factory: Optional[Callable] = None
    ):
        self.check_interval = check_interval
        self.db_session_factory = db_session_factory
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
    async def start(self):
        self.is_running = True
        logger.info("CCTV monitor started")
        
        while self.is_running:
            db = None
            try:
              
                db = self.db_session_factory()
            
                cctv_repo = CctvRepository(db)
                history_repo = HistoryRepository(db)
                user_repo = UserRepository(db)
                notification_repo = NotificationRepository(db)
                
                notif_service = NotificationService(
                    notification_repo, history_repo, cctv_repo, user_repo
                )
                stream_service = MediaMTXService(
                    cctv_repository=cctv_repo,
                    history_repository=history_repo,
                    notification_service=notif_service
                )
                
                logger.info(" Mengecek service stream...")
                await stream_service.get_all_streams_status()

                db.commit()
                
            except asyncio.CancelledError:
                logger.info("Monitor task dibatalkan")
                break
                
            except Exception as e:
                logger.error(f"Error in CCTV monitor: {e}", exc_info=True)
                if db:
                    db.rollback()
                await asyncio.sleep(50)
                
            finally:
                if db:
                    db.close()

            if self.is_running:
                await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        logger.info("Stopping CCTV monitor...")
        self.is_running = False