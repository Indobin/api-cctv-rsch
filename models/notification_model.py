from.base import Base, Column, relationship, ForeignKey, Integer, Boolean

class Notification(Base):
    __tablename__ = "notification"

    id_notification = Column(Integer, primary_key=True)
    is_read = Column(Boolean)
    id_history = Column(Integer, ForeignKey("history.id_history"))
    id_user = Column(Integer, ForeignKey("users.id_user"))

    # relasi ke history
    history = relationship("History", back_populates="notifications")
    # relasi ke user
    user = relationship("User", back_populates="notifications")