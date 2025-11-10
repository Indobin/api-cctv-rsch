from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from jose.exceptions import JWEError
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
import secrets
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise ValueError("SECRET_KEY harus diset di .env dan minimal 32 karakter!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 6000
REFRESH_TOKEN_EXPIRE_DAYS = 7
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None)-> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
def verify_token(token: str, token_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise JWTError(f"Token type mismatch: expected {token_type}")
        return payload
    except JWTError as e:
        raise JWEError(f"Token tidak valid: {str(e)}")
