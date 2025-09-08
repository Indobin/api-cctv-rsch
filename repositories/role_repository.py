from.base import Session, Role, RoleCreate

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int=0, limit: int = 10):
        return self.db.query(Role).offset(skip).limit(limit).all()

    def get_by_id(self, id_role: int):
        return self.db.query(Role).filter(Role.id_role == id_role).first

    def get_by_name(self, nama_role=str):
        return self.db.query(Role).filter(Role.nama_role == nama_role).first()
    
    def create(self, role: RoleCreate):
        db_role = Role(**role.dict())
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role