import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base
# Loads user model and register its table with Base.metadata
from app.models.user import User as UserModel 
from contextlib import contextmanager

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("database_url should not be None")

engine = create_engine(database_url)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False)

def get_db():
    """Provide a database session and close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def transaction(db: Session):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise