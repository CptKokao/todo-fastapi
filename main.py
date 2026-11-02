from uuid import uuid4

from fastapi import FastAPI,status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()
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

@app.get("/tasks")
async def get_tasks() -> list[TaskSchema]: return tasks

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_tasks(playload:TaskCreateSchema ) -> TaskSchema:
    new_tasks = TaskSchema(id=str(uuid4()), title=playload.title, completed=False)
    tasks.append(new_tasks)
    return new_tasks

@app.patch("/tasks/{task_id}")
async def update_task(task_id:str, playload: TaskUpdateSchema):
    for task in tasks:
        if task.id == str(task_id):
            if playload.title:
                task.title = playload.title
            if playload.completed is not None:
                task.completed = playload.completed
            return task

    return None

@app.delete("/tasks/{task_id}", status_code=status.NoContent)
async def delete_task(task_id:str, playload: TaskUpdateSchema):
async def delete_task(task_id: str):
    for task in tasks:
        if task.id == str(task):
            tasks.remove(task)

        return task

    return None