from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column
from app.core.config import get_settings

config = get_settings()
engine = create_engine(config.DATABASE_URL)
session_factory = sessionmaker[Session](engine)

def get_db():
    db = session_factory()
    try:
        yield db
    finally:
        db.close()