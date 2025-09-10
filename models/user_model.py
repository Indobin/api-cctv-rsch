from.base import Base, Column, Integer, String, ForeignKey, DateTime, relationship, func

class User(Base):
    __tablename__ = "users"
    id_user = Column(Integer, primary_key=True, index=True)
    nama = Column(String(200), index=True)
    nip = Column(String(20), unique=True)
    username = Column(String(200), unique=True)
    password = Column(String(255))
    id_role = Column(Integer, ForeignKey("role.id_role"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # Relationship
    # relasi ke role
    role = relationship("Role", back_populates="users")
    # relasi ke notification
    notifications = relationship("Notification", back_populates="user")
    
    @property
    def user_role_name(self):
        return self.role.nama_role if self.role else None