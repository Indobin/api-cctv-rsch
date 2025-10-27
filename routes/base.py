from fastapi import APIRouter, Depends, File, UploadFile, Query, Request
from sqlalchemy.orm import Session
from database import get_db
from core.auth import all_roles
from core.response import success_response
from fastapi.responses import FileResponse

from repositories.user_repository import UserRepository
from repositories.role_repository import RoleRepository
from repositories.location_repository import LocationRepository
from repositories.cctv_repository import CctvRepository
from repositories.notification_repository import NotificationRepository
from repositories.history_repository import HistoryRepository
