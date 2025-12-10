from.base import Session, Notification
from typing import List

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id:int, history_id:int) -> Notification:
        notification = Notification(
            id_history = history_id,
            id_user = user_id
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification
    
    def get_by_user(self, user_id: int, limit: int = 500) -> List[Notification]:
        return self.db.query(Notification).filter(
            Notification.id_user == user_id
        ).order_by(Notification.id_notification.desc()).limit(limit).all()
    
    def delete(self, notification_id: int, user_id: int):
        notification = self.db.query(Notification).filter(
            Notification.id_notification == notification_id,
            Notification.id_user == user_id
        ).first()
        if notification:
            self.db.delete(notification)
            self.db.commit()
        return notification
    
    def delete_all_by_user(self, user_id: int):
        self.db.query(Notification).filter(
            Notification.id_user == user_id
        ).delete()
        self.db.commit()
    
    def count_by_user(self, user_id: int) -> int:
        return self.db.query(Notification).filter(
            Notification.id_user == user_id
        ).count()
    
