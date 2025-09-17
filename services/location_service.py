from repositories.location_repository import LocationRepository
from schemas.location_schemas import LocationBase, LocationCreate, LocationResponse
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