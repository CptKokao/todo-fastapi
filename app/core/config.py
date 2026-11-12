from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Config:
    DATABASE_URL: str
    CORS_ALLOW_ORIGINS: list[str]



def get_settings() -> Config:
    return Config(
        DATABASE_URL=os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/mydb"),
        CORS_ALLOW_ORIGINS=["http://localhost:3000"]
    )

