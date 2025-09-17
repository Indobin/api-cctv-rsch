from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas.location_schemas import LocationResponse, LocationCreate
from repositories.location_repository import LocationRepository
from services.location_service import LocationService
from core.auth import get_superadmin
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
    current_admin = Depends(get_superadmin)
):
    locations = service.get_all_location(skip, limit)
    return success_response(
            message="Locations retrieved successfully",
            data=locations
        )


@router.post("/", response_model=LocationResponse)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    service: LocationService = Depends(get_location_service),
    current_admin = Depends(get_superadmin)
):
    return service.create_location(location)

