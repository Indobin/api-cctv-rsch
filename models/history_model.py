from.base import Base, Integer, DateTime, String, Boolean, Column, ForeignKey, relationship, func

class History(Base):
    __tablename__ = "history"

    id_history = Column(Integer, primary_key=True)
    id_cctv = Column(Integer, ForeignKey("cctv_camera.id_cctv"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Boolean, default=False)
    note = Column(String(255), nullable=True)
    service = Column(Boolean, default=False)
    # relasi ke cctv
    cctv_camera = relationship("CctvCamera", back_populates="histories")
    # relasi ke notification
    notifications = relationship("Notification", back_populates="history")