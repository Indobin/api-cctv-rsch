from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings
from dotenv import load_dotenv
import subprocess
import os
from datetime import datetime
from fastapi import HTTPException, status

load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")

DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
class DatabaseService:
    def export_sql(self, table_name: str | None = None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        if table_name:
            filename = f"{table_name}_dump_{timestamp}.sql"
            table_arg = ["-t", table_name]
        else:
            filename = f"full_db_dump_{timestamp}.sql"
            table_arg = []
        
        file_path = os.path.join("/tmp", filename)
        
        env_vars = os.environ.copy()
        
        if settings.DB_PASSWORD:
            env_vars["PGPASSWORD"] = settings.DB_PASSWORD
        
        command = [
            "pg_dump",
            f"-d{settings.DB_NAME}",
            f"-U{settings.DB_USER}",
            f"-h{settings.DB_HOST}",
            f"-p{settings.DB_PORT}",
            "-a",
            *table_arg,
            "-f",
            file_path
        ]
        try:
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True,
                env=env_vars
            )
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
                                
            return file_path
        
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="pg_dump command not found. Is PostgreSQL installed and in PATH?"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database export failed: {str(e)}"
            )