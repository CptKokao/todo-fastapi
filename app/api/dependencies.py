from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column
from cache.redis import RedisCache
from core.config import get_settings
from db.session import get_db
from services.task import TaskService


TASKS_CACHE_KEY = "tasks:all"


def get_redis_cache() -> RedisCache:
    return RedisCache(get_settings().REDIS_URL)


def get_task_service(
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_redis_cache),
) -> TaskService:
    return TaskService(db, cache, TASKS_CACHE_KEY)
