from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from enum import IntEnum
from typing import List

from database import get_db
from repositories.user_repository import UserRepository
from core.security import SECRET_KEY, ALGORITHM
# class UserRole(IntEnum):
#     SuperAdmin = 1
#     Security = 2

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

user_cache = {}
CACHE_EXPIRE_MINUTES = 5

def get_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM],
            options={"verify_exp": True}
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError:
        raise credentials_exception

    if user_id in user_cache:
        cached_user, expire_time = user_cache[user_id]
        if datetime.now() < expire_time:
            return cached_user
            
    user = UserRepository(db).get_by_id(int(user_id))
    if user is None:
        raise credentials_exception
        
    user_safe = {
        "id_user": user.id_user,
        "nama": user.nama,
        "id_role": user.id_role,
        # Tambahkan semua field yang Anda butuhkan di dependency
    }
    # -----------------------------------------------------------
        
    user_cache[user_id] = (
        user_safe, # Simpan objek yang AMAN (Pydantic/dict)
        datetime.now() + timedelta(minutes=CACHE_EXPIRE_MINUTES)
    )
    
    return user_safe

def superadmin_role(current_user = Depends(get_user)):
    if current_user['id_role'] != 1:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

def all_roles(current_user = Depends(get_user)):
    if current_user['id_role'] not in [1, 2]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
