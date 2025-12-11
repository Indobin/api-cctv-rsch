from repositories.history_repository import HistoryRepository
from repositories.cctv_repository import CctvRepository
from repositories.user_repository import UserRepository
from fastapi import HTTPException, status
from datetime import date, datetime
from io import BytesIO
# from xlsxwriter import Workbook
import pandas as pd
import pytz
from schemas.history_schemas import HistoryCreate, HistoryUpdate

class HistoryService:
    def __init__(
        self,
        history_repo: HistoryRepository,
        cctv_repo: CctvRepository,
        user_repo: UserRepository
    ):
        self.history_repo = history_repo
        self.cctv_repo = cctv_repo
        self.user_repo = user_repo

    def get_all_hisotries(self, skip: int = 0, limit: int = 1000):
        return self.history_repo.get_all(skip, limit)
        
    def create_history(self, history: HistoryCreate):
        existing_cctv = self.cctv_repo.get_by_id(history.id_cctv)
        if not existing_cctv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Id CCTV tidak ada"
            )
        db_history = self.history_repo.create(history)
        db_cctv = self.cctv_repo.get_by_id(db_history.id_cctv)
        db_history.cctv_name = db_cctv.titik_letak
        return db_history
        
    def update_history(self, history_id: int, history: HistoryUpdate):
        existing_history = self.history_repo.get_by_id(history_id)
        if not existing_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Id History tidak ada"
            )
        db_history = self.history_repo.update(history_id, history)
        db_cctv = self.cctv_repo.get_by_id(db_history.id_cctv)
        db_history.cctv_name = db_cctv.titik_letak
        return db_history
        
    def export_history(self, start_date: date, end_date: date, nama_user: str):
        wib_tz = pytz.timezone('Asia/Jakarta')
        data = self.history_repo.get_all_fox_export(start_date, end_date)
        df = pd.DataFrame([dict(row._mapping) for row in data])
        if 'created_at' in df.columns:
                    df['created_at'] = df['created_at'].dt.tz_localize(None)
        if 'service' in df.columns:
                    df['service'] = df['service'].map({True: 'Sudah diperbaiki', False: 'Belum diperbaiki'})
        if 'status' in df.columns:
                    df['status'] = df['status'].map({True: 'Online', False: 'Offline'})
        df.rename(columns={
            "titik_letak": "Titik Letak",
            "ip_address": "Ip Address",
            "nama_lokasi": "Lokasi Dvr",
            "status": "Status Cctv",
            "service": "Status Perbaikan",
            "note": "Catatan",
            "created_at": "Tanggal dan Waktu",
        }, inplace=True)
        current_wib_time = datetime.now(wib_tz)
        metadata = [
            ["Laporan Kerusakan CCTV"],
            [f"Periode: {start_date} sampai {end_date}"],
            [f"Dibuat oleh: {nama_user}"],
            [f"Tanggal Ekspor: {current_wib_time.strftime('%Y-%m-%d %H:%M:%S')}"],
            ["", ""]
        ]

        df_metadata = pd.DataFrame(metadata, columns=["Keterangan", "Nilai"])
        # unique_time = datetime.now().strftime("%Y%m%d%H%M%S") 
            
        output = BytesIO() 
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            sheet_name = "Laporan Kerusakan CCTV"
            df_metadata.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0, header=False)
        # df.to_excel(output, index=False)
            start_row = len(metadata) 

            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row)
        output.seek(0)

        return {
            "data": output, 
            "filename": f"Laporan_kerusakan_dari_{start_date}_sampai_{end_date}.xlsx",
            "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
