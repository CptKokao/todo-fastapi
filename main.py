from select import select
from uuid import uuid4

from fastapi import FastAPI,status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, Session, mapped_column
from contextlib import asynccontextmanager


# DATABASE_URL="postgresql+psycopg://postgres:admin@localhost:5432/auth-postgres"
DATABASE_URL="postgresql+psycopg://root:123456@localhost:5433/db_jwt"

engine = create_engine(DATABASE_URL)
session_factory = sessionmaker[Session](engine)

class Base(DeclarativeBase):
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda :str(uuid4()))

class TaskORM(Base):
    __tablename__ = "tasks"

    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


def get_db():
    db = session_factory()

    try:
        yield db
    finally:
        db.close()
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
)

class TaskSchema(BaseModel):
    id: str
    title: str
    completed: bool

class TaskCreateSchema(BaseModel):
    title: str

class TaskUpdateSchema(BaseModel):
    title: str | None = None
    completed: bool | None = False


tasks: list[TaskSchema] = []

def task_orm_to_model (task_orm: TaskORM) -> TaskSchema:
    return TaskSchema(id=task_orm.id, title=task_orm.title, completed=task_orm.completed)

@app.get("/tasks")
async def get_tasks(db: Session = Depends(get_db)) -> list[TaskSchema]:
    tasks_from_db = db.query(TaskORM).all()
    return [task_orm_to_model(task) for task in tasks_from_db]

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_tasks(playload:TaskCreateSchema, db: Session = Depends(get_db)) -> TaskSchema:
    new_tasks = TaskORM(title=playload.title, completed=False)
    db.add(new_tasks)
    db.commit()

    return task_orm_to_model(new_tasks)

@app.patch("/tasks/{task_id}")
async def update_task(task_id:str, playload: TaskUpdateSchema, db: Session = Depends(get_db)) -> TaskSchema:
    task_for_update = db.get(TaskORM, task_id)

    if playload.title:
        task_for_update.title = playload.title
    if playload.completed is not None:
        task_for_update.completed = playload.completed

    db.commit()

    return task_orm_to_model(task_for_update)



@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id:str, playload: TaskUpdateSchema, db: Session = Depends(get_db)):
    task_for_update = db.get(TaskORM, task_id)

    db.delete(task_for_update)
    db.commit()

    return None