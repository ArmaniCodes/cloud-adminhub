from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    __table_args__ = ( CheckConstraint("role IN ('admin','support','viewer')"),
                       )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable = False)
    email: Mapped[str] = mapped_column(nullable = False, unique = True) 
    role: Mapped[str] = mapped_column(nullable = False)