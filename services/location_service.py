from repositories.location_repository import LocationRepository
from schemas.location_schemas import LocationCreate, LocationUpdate
from fastapi import HTTPException, status
class LocationService:
    def __init__(self, location_repository: LocationRepository):
        self.location_repository = location_repository

    def get_all_location(self, skip: int = 0, limit: int = 50 ):
        return self.location_repository.get_all(skip, limit)
    
    def create_location(self, location: LocationCreate):
        exiting_name = self.location_repository.get_by_name(location.nama_lokasi)
        if exiting_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lokasi sudah ada"
            )
        return self.location_repository.create(location)
    
    def update_location(self, location_id:int, location: LocationUpdate):
        db_location = self.location_repository.get_by_id(location_id)
        if not db_location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Id lokasi tidak ditemukan"
            )
        if location.nama_lokasi:
            existing_location = self.location_repository.get_by_name(location.nama_lokasi)
            if existing_location and existing_location.id_location != location_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nama lokasi sudah ada"
                )
        return self.location_repository.update(location_id, location)
    
    def hard_delete_location(self, location_id:int):
        location = self.location_repository.hard_delete(location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lokasi dengan id {location_id} tidak ditemukan"
            )
        return location