from.base import Session, Location
from datetime import datetime
from zoneinfo import ZoneInfo

class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int=0, limit: int = 10):
        return self.db.query(Location).where(Location.deleted_at == None).offset(skip).limit(limit).all()

    def get_by_id(self, id_location: int):
        return self.db.query(Location).filter(Location.id_location == id_location).first()

    def get_by_name(self, nama_lokasi=str):
        return self.db.query(Location).filter(Location.nama_lokasi == nama_lokasi).where(Location.deleted_at == None).first()

    def create(self, location: Location):
        db_location = Location(
            nama_lokasi = location.nama_lokasi
        )
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location
    
    def create_by_analog(self, nama_lokasi: str):
        db_location = Location(nama_lokasi=nama_lokasi)
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location
    
    def update(self, location_id, location: Location):
        db_location = self.get_by_id(location_id)
        if not db_location:
            return None
        if location.nama_lokasi:
            db_location.nama_lokasi = location.nama_lokasi
        self.db.commit()
        self.db.refresh(db_location)
        return db_location
    
    def soft_delete(self, location_id:int):
        db_location = self.get_by_id(location_id)
        if not db_location:
            return None
        utc_now = datetime.now(ZoneInfo("UTC"))
        db_location.deleted_at = utc_now
        self.db.commit()
        self.db.refresh(db_location)
        return db_location
    
    
    def hard_delete(self, location_id:int):
        db_location = self.get_by_id(location_id)
        if not db_location:
            return None
        self.db.delete(db_location)
        self.db.commit()
        return db_location
    
    def get_existing_locations(self, names: list[str]) -> dict:
        result = (
            self.db.query(Location)
            .filter(Location.nama_lokasi.in_(names))
            .where(Location.deleted_at == None)
            .all()
        )
        return {loc.nama_lokasi: loc for loc in result}

    
    def bulk_create(self, location_names: list[str]):
        db_locations = [Location(nama_lokasi=name) for name in location_names]
        self.db.add_all(db_locations)
        self.db.commit()
        return db_locations