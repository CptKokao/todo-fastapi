from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    DATABASE_URL: str
    CORS_ALLOW_ORIGINS: list[str]


def get_settings() -> Config:
    return Config(
        DATABASE_URL="postgresql+psycopg://root:123456@localhost:5433/db_jwt",
        CORS_ALLOW_ORIGINS=["http://localhost:3000"]
    )