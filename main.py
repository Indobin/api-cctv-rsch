from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import user_route, auth_router, role_router, location_route, cctv_router, mediamtx_router
from models.user_model import User
from models.role_model import Role
from models.notification_model import Notification
from models.history_model import History
from models.location_model import Location
from models.cctv_model import CctvCamera


Base.metadata.create_all(bind=engine)

app = FastAPI(title="CMS RSCH Management API", version="1.0.0")
origins = [
    "http://localhost:3000",  # Alamat frontend React saat development
    "http://localhost:5173",  # Alamat frontend Vite/React saat development
    "http://localhost:8080",  # Alamat frontend Vue.js saat development
    "https://domain-frontend-anda.com",  # Alamat frontend Anda saat sudah di-deploy (produksi)
]

# Tambahkan CORSMiddleware ke aplikasi
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Mengizinkan origin yang ada di daftar 'origins'
    allow_credentials=True,  # Mengizinkan cookies dikirimkan
    allow_methods=["*"],  # Mengizinkan semua metode HTTP (GET, POST, PUT, dll.)
    allow_headers=["*"],  # Mengizinkan semua header HTTP
)

app.include_router(user_route.router)
app.include_router(auth_router.router)
app.include_router(role_router.router)
app.include_router(location_route.router)
app.include_router(cctv_router.router)
app.include_router(mediamtx_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to User Management API"}
