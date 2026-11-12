from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    DATABASE_URL: str
    REDIS_URL: str
    CORS_ALLOW_ORIGINS: list[str]
    cache_tasks_key:str


def get_settings() -> Config:
    return Config(
        DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/mydb"),
        REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        CORS_ALLOW_ORIGINS=["http://localhost:3000"],
        cache_tasks_key="cache:tasks_list"
    )

