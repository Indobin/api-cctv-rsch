from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.cctv_schemas import CctvResponse, CctvCreate
from repositories.cctv_repository import CctvRepository
from services.cctv_service import CctvService
from core.auth import get_superadmin
from core.response import success_response
import subprocess
import os
import uuid
from typing import List

router = APIRouter(prefix="/cctv", tags=["cctv"])


def get_cctv_service(db: Session = Depends(get_db)):
    cctv_repository = CctvRepository(db)
    return CctvService(cctv_repository)

@router.get("/")
def read_cctv(
    skip: int = 0,
    limit: int = 50,
    service: CctvService = Depends(get_cctv_service),
    current_admin = Depends(get_superadmin)
):
    cctvs = service.get_all_cctv(skip, limit)
    return success_response(
            message="Cctv retrieved successfully",
            data=cctvs
        )


@router.post("/")
def create_user(
    cctv: CctvCreate,
    db: Session = Depends(get_db),
    service: CctvService = Depends(get_cctv_service),
    current_admin = Depends(get_superadmin)
):
    cctvs = service.create_cctv(cctv)
    return success_response(
            message="Cctv retrieved successfully",
            data=cctvs
        )

@router.post("/stream/start_multiple/")
async def start_multiple_streams(cctv_ids: List[int], db: Session = Depends(get_db)):
    repo = CctvRepository(db)
    hls_urls = []
    
    for cctv_id in cctv_ids:
        cctv = repo.get_by_id(cctv_id)  # Ambil RTSP URL dari database
        if not cctv:
            continue
        
        # Jika stream sudah aktif, kembalikan URL yang ada
        if cctv_id in ACTIVE_STREAMS:
            hls_urls.append({"id": cctv_id, "url": f"/{STATIC_DIR}/{cctv_id}/stream.m3u8"})
            continue
            
        # Buat direktori untuk stream HLS jika belum ada
        output_dir = os.path.join(STATIC_DIR, str(cctv_id))
        os.makedirs(output_dir, exist_ok=True)
        
        # Konstruksi perintah FFmpeg
        rtsp_url = cctv.ip_address  # Asumsikan model CCTV memiliki atribut rtsp_url
        output_path = os.path.join(output_dir, "stream.m3u8")
        
        # Perintah FFmpeg untuk konversi RTSP ke HLS
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", rtsp_url,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-hls_time", str(HLS_TIME),
            "-hls_list_size", str(HLS_LIST_SIZE),
            "-hls_segment_filename", os.path.join(output_dir, "segment_%03d.ts"),
            "-hls_flags", "delete_segments",
            "-start_number", "0",
            "-f", "hls",
            output_path
        ]
        
        # Jalankan FFmpeg sebagai subprocess
        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # Simpan proses ke dictionary aktif
            ACTIVE_STREAMS[cctv_id] = {
                "process": process,
                "output_dir": output_dir
            }
            
            hls_urls.append({"id": cctv_id, "url": f"/{STATIC_DIR}/{cctv_id}/stream.m3u8"})
            
        except Exception as e:
            print(f"Failed to start stream for CCTV {cctv_id}: {e}")
            # Hapus direktori jika gagal
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            
    return {"streams": hls_urls}


@router.post("/stream/stop/{cctv_id}")
async def stop_stream(cctv_id: int):
    if cctv_id in ACTIVE_STREAMS:
        process_info = ACTIVE_STREAMS[cctv_id]
        process = process_info["process"]
        
        # Hentikan proses FFmpeg dengan graceful shutdown
        try:
            process.stdin.write(b"q")
            process.stdin.flush()
        except:
            process.terminate()
        
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Hapus dari dictionary aktif
        del ACTIVE_STREAMS[cctv_id]
        
        # Hapus file HLS (opsional)
        import shutil
        shutil.rmtree(process_info["output_dir"], ignore_errors=True)
        
        return {"message": f"Stream for CCTV {cctv_id} stopped successfully"}
    
    return {"message": f"No active stream found for CCTV {cctv_id}"}


# @router.get("/stream/status/")
# async def get_stream_status():
#     statuses = {}
#     for cctv_id, process_info in ACTIVE_STREAMS.items():
#         process = process_info["process"]
#         statuses[cctv_id] = {
#             "status": "running" if process.poll() is None else "stopped",
#             "output_dir": process_info["output_dir"]
#         }
#     return statuses
#     repo = CctvRepository(db)
#     hls_urls = []
    
#     for cctv_id in cctv_ids:
#         cctv = repo.get_by_id(cctv_id) # Ambil RTSP URL dari database
#         if not cctv:
#             continue
        
#         # Lanjutkan logika start stream seperti di jawaban sebelumnya
#         if cctv_id in active_streams:
#             hls_urls.append({"id": cctv_id, "url": f"/{STATIC_DIR}/{cctv_id}/stream.m3u8"})
#             continue
            
#         # Logika untuk menjalankan subprocess ffmpeg
#         try:
#             # ... (kode untuk menjalankan ffmpeg)
#             # Anda perlu mengimplementasikan ini di sini atau di fungsi terpisah.
#             # Jangan lupa menyimpan subprocess di active_streams
            
#             hls_urls.append({"id": cctv_id, "url": f"/{STATIC_DIR}/{cctv_id}/stream.m3u8"})
#         except Exception as e:
#             print(f"Failed to start stream for CCTV {cctv_id}: {e}")
            
#     return {"streams": hls_urls}