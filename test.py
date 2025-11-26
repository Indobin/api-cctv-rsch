import uuid

@staticmethod
def parse_import_cctv(uploaded_file):
    try:
        contents = uploaded_file.file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Langsung convert ke dict (lebih cepat dari iterrows)
        rows = df.rename(columns={
            "Titik Letak": "titik_letak",
            "Ip Address": "ip_address",
            "Server Monitoring": "server_monitoring"
        }).to_dict('records')
        
        return rows
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error saat membaca file: {str(e)}"
        )
    finally:
        uploaded_file.file.close()


def import_cctvs(self, rows: list[dict]):
    # Akses db dari repository
    db = self.cctv_repository.db
    
    imported_cctvs = []
    updated_cctvs = []
    
    # 1. BULK QUERY: Ambil semua data sekaligus
    server_names = list(set(row["server_monitoring"] for row in rows))
    ip_addresses = [row["ip_address"] for row in rows]
    titik_letaks = [row["titik_letak"] for row in rows]
    
    # Query lokasi yang sudah ada (pakai db dari repository)
    from models.location import Location  # Import model Location
    existing_locations_query = db.query(Location)\
        .filter(Location.nama_lokasi.in_(server_names))\
        .all()
    existing_locations = {loc.nama_lokasi: loc for loc in existing_locations_query}
    
    # Query CCTV yang sudah ada
    from models.cctv import Cctv  # Import model Cctv
    existing_cctvs_by_ip_query = db.query(Cctv)\
        .filter(Cctv.ip_address.in_(ip_addresses))\
        .filter(Cctv.deleted_at == None)\
        .all()
    existing_cctvs_by_ip = {cctv.ip_address: cctv for cctv in existing_cctvs_by_ip_query}
    
    existing_cctvs_by_position_query = db.query(Cctv)\
        .filter(Cctv.titik_letak.in_(titik_letaks))\
        .filter(Cctv.deleted_at == None)\
        .all()
    existing_cctvs_by_position = {cctv.titik_letak: cctv for cctv in existing_cctvs_by_position_query}
    
    # 2. PROSES: Buat lokasi baru jika perlu (pakai repository)
    for server_name in server_names:
        if server_name not in existing_locations:
            # Gunakan repository untuk create location
            new_loc = self.location_repository.create(
                location=type("LocationCreate", (), {"nama_lokasi": server_name})
            )
            existing_locations[server_name] = new_loc
    
    # 3. PROSES: Siapkan data CCTV untuk insert/update
    for row in rows:
        lokasi = existing_locations[row["server_monitoring"]]
        
        # Cek apakah CCTV sudah ada
        existing = (
            existing_cctvs_by_ip.get(row["ip_address"]) or 
            existing_cctvs_by_position.get(row["titik_letak"])
        )
        
        cctv_data = {
            "titik_letak": row["titik_letak"],
            "ip_address": row["ip_address"],
            "id_location": lokasi.id_location,
        }
        
        if existing:
            # Cek apakah ada perubahan data
            needs_update = (
                existing.titik_letak != row["titik_letak"] or
                existing.ip_address != row["ip_address"] or
                existing.id_location != lokasi.id_location
            )
            
            if needs_update:
                # Gunakan repository untuk update
                updated = self.cctv_repository.update(existing.id_cctv, cctv_data)
                updated_cctvs.append(updated)
        else:
            # Gunakan repository untuk create
            stream_key = f"loc_{lokasi.id_location}_cam_{uuid.uuid4().hex[:8]}"
            cctv_data["stream_key"] = stream_key
            new_cctv = self.cctv_repository.create(cctv_data)
            imported_cctvs.append(new_cctv)
    
    return {
        "imported": imported_cctvs,
        "updated": updated_cctvs
    }


def import_cctvs(self, rows: list[dict]):
    db = self.cctv_repository.db
    # ... kode bulk query tetap sama ...
    
    # Buat lokasi baru (bulk)
    new_location_names = [name for name in server_names if name not in existing_locations]
    if new_location_names:
        new_locs = self.location_repository.bulk_create(new_location_names)
        for loc in new_locs:
            existing_locations[loc.nama_lokasi] = loc
    
    # Siapkan data untuk bulk insert/update
    cctvs_to_create = []
    cctvs_to_update = []
    
    for row in rows:
        lokasi = existing_locations[row["server_monitoring"]]
        existing = existing_cctvs_by_ip.get(row["ip_address"]) or existing_cctvs_by_position.get(row["titik_letak"])
        
        cctv_data = {
            "titik_letak": row["titik_letak"],
            "ip_address": row["ip_address"],
            "id_location": lokasi.id_location,
        }
        
        if existing:
            needs_update = (
                existing.titik_letak != row["titik_letak"] or
                existing.ip_address != row["ip_address"] or
                existing.id_location != lokasi.id_location
            )
            if needs_update:
                cctvs_to_update.append((existing.id_cctv, cctv_data))
        else:
            cctv_data["stream_key"] = f"loc_{lokasi.id_location}_cam_{uuid.uuid4().hex[:8]}"
            cctvs_to_create.append(cctv_data)
    
    # Bulk insert & update (1 commit!)
    imported_cctvs = self.cctv_repository.bulk_create(cctvs_to_create) if cctvs_to_create else []
    updated_cctvs = self.cctv_repository.bulk_update(cctvs_to_update) if cctvs_to_update else []
    
    return {"imported": imported_cctvs, "updated": updated_cctvs}