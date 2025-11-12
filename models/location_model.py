from.base import Base, relationship, Column, Integer, String, DateTime, Index
class Location(Base):
    __tablename__ = "location"

    id_location = Column(Integer, primary_key=True)
    nama_lokasi = Column(String(200))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
            Index(
                'uq_lokasi_active', 
                'nama_lokasi', 
                unique=True, 
                postgresql_where=Column('deleted_at') == None,
            ),
        )
    # relasi ke cctv_camera
    cctv_cameras = relationship("CctvCamera", back_populates="location", passive_deletes=True)