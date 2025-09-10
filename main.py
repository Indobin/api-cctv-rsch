from fastapi import FastAPI
from database import engine, Base
from routes import user_route, auth_router, role_router
from models.user_model import User
from models.role_model import Role
from models.notification_model import Notification
from models.history_model import History
from models.location_model import Location
from models.cctv_model import CctvCamera

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API", version="1.0.0")

app.include_router(user_route.router)
app.include_router(auth_router.router)
app.include_router(role_router.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to User Management API"}