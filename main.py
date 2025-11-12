from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from database import engine, Base, SessionLocal
from routes import (
    auth_route, cctv_route, mediamtx_route, 
    notification_route, role_route, user_route, 
    location_route, history_route
)
# from models import *
from services.monitoring_cctv import BackgroundCCTVMonitor

logging.basicConfig(level=logging.INFO, 
                    format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger()

Base.metadata.create_all(bind=engine)

# background_task = None 

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    logger.info("Starting FastAPI application...")
    
    monitor = BackgroundCCTVMonitor(
        check_interval=40,
        db_session_factory=SessionLocal
    )
   
    monitor_task = asyncio.create_task(monitor.start())
    app.state.monitor_task = monitor_task
    app.state.monitor = monitor
    
    logger.info("Background CCTV start")
    
    yield
    # Cleanup on shutdown
    logger.info("Shutting down...")
    await monitor.stop()
    
    if monitor_task and not monitor_task.done():
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Shutdown complete")
    
app = FastAPI(
title="CMS RSCH Management API",
 version="1.0.0",   
lifespan=lifespan
)
# app = FastAPI(title="CMS RSCH Management API", version="1.0.0")
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
    return {
        "message": "Welcome to CMS RSCH Management API",
        "version": "1.0.0",
        "status": "running"
    }
