from app.models.base import Base
from sqlalchemy import DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    actor_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    action: Mapped[str] = mapped_column(nullable=False)
    
    target_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    created_at: Mapped[datetime] =  mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    details: Mapped[str] = mapped_column(Text, nullable=False)