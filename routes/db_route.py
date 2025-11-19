from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.responses import FileResponse
import os
from database import DatabaseService
from core.auth import superadmin_role
router = APIRouter(prefix="/db", tags=["Database Management"])

@router.get("/export/sql")
def export_sql_data(
    table_name: str = Query(None, description="Nama tabel yang ingin diekspor (kosongkan untuk semua data)"),
    service = DatabaseService(),
    # Hanya Superadmin yang boleh melakukan dump DB
    user_role = Depends(superadmin_role) 
):
    try:
        file_path = service.export_sql(table_name=table_name)
        filename = os.path.basename(file_path)
        
        return FileResponse(
            file_path, 
            filename=filename, 
            media_type="application/sql"
            # Optional: Jika Anda ingin menghapus file setelah dikirim
            # background=BackgroundTask(lambda: os.remove(file_path)) 
        )
        
    except HTTPException as e:
        # Menangkap error dari service
        raise e
    except Exception as e:
        # Menangkap error lain
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")