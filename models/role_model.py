from.base import Base, Column, Integer, String, relationship, func

class Role(Base):
    __tablename__ = "role"

    id_role = Column(Integer, primary_key=True, index=True)
    nama_role= Column(String(100), unique=True, index=True)

    
    # relasi ke users
    users = relationship("User", back_populates="role")
