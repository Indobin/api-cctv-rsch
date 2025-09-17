from.base import Base, relationship, Column, Integer, String

class Location(Base):
    __tablename__ = "location"

    id_location = Column(Integer, primary_key=True)
    nama_lokasi = Column(String(200), unique=True)

    # relasi ke cctv_camera
    cctv_cameras = relationship("CctvCamera", back_populates="location")