from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from database import get_db
from repositories.user_repository import UserRepository
from core.security import SECRET_KEY, ALGORITHM

def get_user(token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = UserRepository(db).get_by_id(int(user_id))
    if user is None:
        raise credentials_exception
    return user

def get_superadmin(current_user = Depends(get_user)):
    if current_user.id_role != 1:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
