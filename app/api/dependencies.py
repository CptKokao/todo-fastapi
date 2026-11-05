from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column
from app.db.session import get_db
from app.services.task import TaskService


def get_task_service(db: Session = Depends(get_db)):
    return TaskService(db)
