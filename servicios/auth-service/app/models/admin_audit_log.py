from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .user import Base


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, index=True, nullable=False)
    actor_email = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_user_id = Column(Integer, index=True, nullable=True)
    target_email = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
