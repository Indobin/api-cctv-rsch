from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio
from typing import Optional

from database import engine, Base, SessionLocal
from routes import auth_route, cctv_route, mediamtx_route, notification_route, role_route, user_route, location_route, history_route
# from models import *
from models.user_model import User
from models.role_model import Role
from models.notification_model import Notification
from models.history_model import History
from models.location_model import Location
from models.cctv_model import CctvCamera
from services.mediamtx_service import MediaMTXService
from repositories.cctv_repository import CctvRepository
from repositories.history_repository import HistoryRepository
from repositories.user_repository import UserRepository
from repositories.history_repository import HistoryRepository
from repositories.notification_repository import NotificationRepository
from services.notification_service import NotificationService

logging.basicConfig(level=logging.INFO, 
                    format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger()
Base.metadata.create_all(bind=engine)

# background_task = None 

@asynccontextmanager
async def lifespan(app: FastAPI):
  
    global background_task

    logger.info("Starting FastAPI with background CCTV monitor...")

    # Buat DB session
    db = SessionLocal()

    # Buat repo dan service
    cctv_repo = CctvRepository(db)
    history_repo = HistoryRepository(db)
    user_repo = UserRepository(db)
    notification_repo = NotificationRepository(db)
    notif_service =  NotificationService(notification_repo, history_repo, cctv_repo, user_repo)
    stream_service = MediaMTXService(cctv_repository=cctv_repo, notification_service=notif_service)

    # task di background (loop periodik)
    async def background_cctv_monitor():
        while True:
            try:
                logger.info("Background CCTV monitor running...") 
                await stream_service.get_all_streams_status()
                await asyncio.sleep(40)  # interval
            except asyncio.CancelledError:
                logger.info("CCTV monitor task stopped")
                break
            except Exception as e:
                logger.error(f"❌ Error in background monitor: {e}")
                await asyncio.sleep(50)


    background_task = asyncio.create_task(background_cctv_monitor())
    yield


    logger.info("🧹 Shutting down background task...")
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    db.close()
    logger.info("Shutdown complete")

# app = FastAPI(title="CMS RSCH Management API", version="1.0.0",   lifespan=lifespan)
app = FastAPI(title="CMS RSCH Management API", version="1.0.0")
origins = [
    "http://localhost:3000",  
    "https://domain-frontend.com"
]

#CORSMiddleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Mengizinkan origin yang ada di daftar 'origins'
    allow_credentials=True,  # Mengizinkan cookies dikirimkan
    allow_methods=["*"],  # Mengizinkan semua metode HTTP (GET, POST, PUT, dll.)
    allow_headers=["*"],  # Mengizinkan semua header HTTP
)

app.include_router(user_route.router)
app.include_router(auth_route.router)
app.include_router(role_route.router)
app.include_router(location_route.router)
app.include_router(cctv_route.router)
app.include_router(mediamtx_route.router)
app.include_router(notification_route.router)
app.include_router(history_route.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to User Management API"}
