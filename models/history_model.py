from.base import Base, Integer, DateTime, Column, ForeignKey, relationship, func

class History(Base):
    __tablename__ = "history"

    id_history = Column(Integer, primary_key=True)
    id_cctv = Column(Integer, ForeignKey("cctv_camera.id_cctv"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relasi ke cctv
    cctv_camera = relationship("CctvCamera", back_populates="histories")
    # relasi ke notification
    notifications = relationship("Notification", back_populates="history")