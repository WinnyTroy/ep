
from sqlmodel import SQLModel
from .settings.settings import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.database_url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
