from fastapi import APIRouter, status, Depends, HTTPException
from app.api.dependencies import get_task_service
from app.services.task import TaskService,TaskNotFound
from app.schemas.tasks import TaskSchema,TaskCreateSchema, TaskUpdateSchema


router = APIRouter(prefix="/tasks")

@router.get("")
async def get_tasks(task_service: TaskService = Depends(get_task_service)) -> list[TaskSchema]:
    return task_service.get_tasks()

@router.post("", status_code=status.HTTP_201_CREATED)
def create_tasks(playload:TaskCreateSchema, task_service: TaskService = Depends(get_task_service)) -> TaskSchema:
    return task_service.create_task(playload)

@router.patch("/{task_id}")
async def update_task(task_id:str, playload: TaskUpdateSchema, task_service: TaskService = Depends(get_task_service)) -> TaskSchema:
    try:
        return task_service.update_task(task_id,playload)
    except TaskNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id:str, task_service: TaskService = Depends(get_task_service)):
    try:
        task_service.delete_task(task_id)
        return None
    except TaskNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


