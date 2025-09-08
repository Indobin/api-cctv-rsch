from.base import Session, User, CryptContext, UserCreate, UserUpdate, Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 50):
        return (
            self.db.query(
                User.id,
                User.name,
                User.username,
                User.id_role,
                Role.type.label("user_type_name"),  
                User.created_at,
                User.updated_at,
            )
            .join(Role, User.id_role == Role.id_role)
            .offset(skip)
            .limit(limit)
            .all()
    )

    
    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def create(self, user: UserCreate):
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            name = user.name,
            username = user.username,
            hashed_password = hashed_password,
            user_type_id = 2
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, user: UserUpdate):
        db_user = self.get_by_id(user_id)
        if not db_user:
            return None
        
        if user.name:
            db_user.name = user.name
        if user.username:
            db_user.username = user.username
        if user.password:
            db_user.hashed_password = pwd_context.hash(user.password)
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: int):
        db_user = self.get_by_id(user_id)
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True