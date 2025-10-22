from.base import APIRouter, Depends, Session, get_db, all_roles, success_response
from.base import LocationRepository
from schemas.location_schemas import LocationResponse, LocationCreate, LocationUpdate
from services.location_service import LocationService

router = APIRouter(prefix="/location", tags=["locations"])

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
    response_data = [LocationResponse.from_orm(loc) for loc in locations]
    return success_response(
            message="Daftar semua lokasi",
            data=response_data
        )


@router.post("/", response_model=dict)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    created = service.create_location(location)
    return success_response(
        message="Lokasi berhasil ditambahkan", 
        data=LocationResponse.from_orm(created)
    )

@router.put("/{location_id}")
def update_location(
    location_id: int,
    location: LocationUpdate,
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    updated = service.update_location(location_id, location)
    return success_response(
        message="Lokasi berhasil diperbarui", 
        data=LocationResponse.from_orm(updated)
    )

@router.delete("/", response_model=dict)
def hard_delete_location(
    location_id: int,
    service: LocationService = Depends(get_location_service),
    user_role = Depends(all_roles)
):
    deleted = service.hard_delete_location(location_id)
    return success_response(
        message="Lokasi berhasil dihapus", 
        data=LocationResponse.from_orm(deleted)
    )
