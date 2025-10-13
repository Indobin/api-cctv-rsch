from.base import Base, Column, Integer, String, ForeignKey, DateTime, Boolean, relationship, func

class CctvCamera(Base):
    __tablename__ = "cctv_camera"

    id_cctv = Column(Integer, primary_key=True)
    titik_letak = Column(String)
    ip_address = Column(String)
    stream_key = Column(String, unique=True)
    is_streaming = Column(Boolean, default=False)
    id_location = Column(Integer, ForeignKey("location.id_location", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # relasi ke lokasi
    location = relationship("Location", back_populates="cctv_cameras")
    # relasi ke history
    histories = relationship("History", back_populates="cctv_camera")