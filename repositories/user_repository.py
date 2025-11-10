from.base import Session, User, CryptContext, Role
from sqlalchemy import func
from datetime import datetime
from zoneinfo import ZoneInfo
from core.security import verify_password
from typing import List

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 50):
        return (
            self.db.query(
                User.id_user,
                User.nama,
                User.nip,
                User.username,
                User.id_role,
                Role.nama_role.label("user_role_name"),  
                func.to_char(func.timezone('Asia/Jakarta', User.created_at), 'YYYY-MM-DD HH24:MI:SS').label("created_at"),
                func.to_char(func.timezone('Asia/Jakarta', User.last_login), 'YYYY-MM-DD HH24:MI:SS').label("last_login"),
                func.to_char(func.timezone('Asia/Jakarta', User.deleted_at), 'YYYY-MM-DD HH24:MI:SS').label("deleted_at"),
            )
            .join(Role, User.id_role == Role.id_role)
            .where(User.deleted_at == None)
            .order_by(User.id_user.desc())
            .offset(skip)
            .limit(limit)
            .all()
    )

    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_usernameL(self, username: str):
        return self.db.query(User).filter(User.username == username).where(User.deleted_at == None).first()

    def get_by_nip(self, nip: str):
        return self.db.query(User).filter(User.nip == nip).first()
    
    def get_all_id(self) -> List[int]:
        results = self.db.query(User.id_user).all()
        return [row.id_user for row in results]
    
    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id_user == user_id).first()
    
    def create(self, user: User):
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            nama = user.nama,
            nip = user.nip,
            username = user.username,
            password = hashed_password,
            id_role = 2
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, user: User):
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        
        if user.nama:
            db_user.nama = user.nama
        if user.nip:
            db_user.nip = user.nip
        if user.username:
            db_user.username = user.username
        if user.password:
            db_user.hashed_password = pwd_context.hash(user.password)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def hard_delete(self, user_id: int):
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        
        self.db.delete(db_user)
        self.db.commit()
        return db_user
    
    def soft_delete(self, user_id:int):
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        utc_now = datetime.now(ZoneInfo("UTC"))
        db_user.deleted_at = utc_now
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    
    def get_all_for_export(self):
        return (
            self.db.query(
                User.nama,
                User.username, 
                User.nip,
                User.username.label('password')
            )
            .join(Role, User.id_role == Role.id_role)
            .where(User.id_role == 2)
            .all()
    )

    def last_login(self, user_id:int):
        db_user = self.get_by_id(user_id)
        utc_now = datetime.now(ZoneInfo("UTC"))
        db_user.last_login = utc_now
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
   

        