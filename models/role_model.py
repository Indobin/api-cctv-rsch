from.base import Base, Column, Integer, String, relationship

class Role(Base):
    __tablename__ = "role"

    id_role = Column(Integer, primary_key=True, index=True)
    nama_role= Column(String(50), unique=True, index=True)

    
    # relasi ke users
    users = relationship("User", back_populates="role")
