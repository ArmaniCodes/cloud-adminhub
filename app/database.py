import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from app.models.base import Base
from app.models.user import User # Loads user model and register its table with Base.metadata
 
load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("database_url should not be None")

engine = create_engine(database_url)
Base.metadata.create_all(engine)

