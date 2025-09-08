from fastapi import FastAPI
from database import engine, Base
from routes import user_route

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API", version="1.0.0")

app.include_router(user_route.router)
@app.get("/")
def read_root():
    return {"message": "Welcome to User Management API"}