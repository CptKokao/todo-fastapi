from uuid import uuid4
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda :str(uuid4()))
