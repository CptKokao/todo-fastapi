from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column

from app.models.base import Base

class TaskORM(Base):
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)
