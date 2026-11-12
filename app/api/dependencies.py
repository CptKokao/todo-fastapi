from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column
from db.session import get_db
from services.task import TaskService


def get_task_service(db: Session = Depends(get_db)):
    return TaskService(db)
