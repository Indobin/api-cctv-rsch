from.base import Base, Column, Integer, String, BigInteger,  ForeignKey, DateTime, Index, relationship, func
class User(Base):
    __tablename__ = "users"
    id_user = Column(Integer, primary_key=True, index=True)
    nama = Column(String(50), index=True)
    nip = Column(String(18))
    username = Column(String(50))
    password = Column(String(255))
    id_role = Column(Integer, ForeignKey("role.id_role"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # Relationship
    # relasi ke role
    role = relationship("Role", back_populates="users")
    # relasi ke notification
    notifications = relationship("Notification", back_populates="user")
    __table_args__ = (
            
            Index(
                'uq_username_active', 
                'username', 
                unique=True, 
                postgresql_where=Column('deleted_at') == None,
            ),

            Index(
                'uq_nip_active', 
                'nip', 
                unique=True, 
                postgresql_where=Column('deleted_at') == None,
            ),
        )
    
    @property
    def user_role_name(self):
        return self.role.nama_role if self.role else None