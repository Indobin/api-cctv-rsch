from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models.role_model import Role
from models.user_model import User
from models.location_model import Location
from models.cctv_model import CctvCamera

from schemas.role_schemas import RoleCreate
from schemas.user_schemas import UserCreate, UserUpdate
from schemas.cctv_schemas import CctvCreate, CctvUpdate
from schemas.location_schemas import LocationCreate



        