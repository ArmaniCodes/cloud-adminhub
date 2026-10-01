from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    __table_args__ = ( 
        CheckConstraint(
            "role IN ('admin', 'support', 'viewer')",
            name="ck_users_role"
        ),
        UniqueConstraint("email",name="uq_users_email"),
     )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable = False)
    email: Mapped[str] = mapped_column(nullable = False) 
    role: Mapped[str] = mapped_column(nullable = False)
    password_hash: Mapped[str]=mapped_column(nullable = False)