import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("database_url should not be None")

engine = create_engine(database_url)

