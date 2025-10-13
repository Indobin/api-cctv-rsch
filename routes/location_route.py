from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.location_schemas import LocationResponse, LocationCreate, LocationUpdate, LocationDelete
from repositories.location_repository import LocationRepository
from services.location_service import LocationService
from core.auth import all_roles
from core.response import success_response

router = APIRouter(prefix="/location", tags=["location"])

def get_location_service(db: Session = Depends(get_db)):
    location_repository = LocationRepository(db)
    return LocationService(location_repository)

@router.get("/")
def read_location(
    skip: int = 0,
    limit: int = 50,
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    locations = service.get_all_location(skip, limit)
    return success_response(
            message="Locations retrieved successfully",
            data=locations
        )


@router.post("/", response_model=dict)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    created = service.create_location(location)
    return success_response("Lokasi berhasil ditambahkan", LocationResponse.from_orm(created))

@router.put("/{location_id}", response_model=dict)
def update_location(
    location_id: int,
    location: LocationUpdate,
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    updated = service.update_location(location_id, location)
    return success_response("Lokasi berhasil diperbarui", LocationResponse.from_orm(updated))

@router.delete("/", response_model=dict)
def hard_delete_location(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    deleted = service.hard_delete_location(location_id)
    return success_response("Lokasi berhasil dihapus", LocationDelete.from_orm(deleted))
