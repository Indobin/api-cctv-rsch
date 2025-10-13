from.base import Session, Location, LocationCreate, LocationUpdate

class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int=0, limit: int = 10):
        return self.db.query(Location).offset(skip).limit(limit).all()

    def get_by_id(self, id_location: int):
        return self.db.query(Location).filter(Location.id_location == id_location).first()

    def get_by_name(self, nama_lokasi=str):
        return self.db.query(Location).filter(Location.nama_lokasi == nama_lokasi).first()
    
    def create(self, location: LocationCreate):
        db_location = Location(
            nama_lokasi = location.nama_lokasi
        )
        self.db.add(db_location)
        self.db.commit()
        self.db.refresh(db_location)
        return db_location
    
    def update(self, location_id, location: LocationUpdate):
        db_location = self.get_by_id(location_id)
        if not db_location:
            return None
        if location.nama_lokasi:
            db_location.nama_lokasi = location.nama_lokasi
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