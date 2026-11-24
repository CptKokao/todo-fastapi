from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_task_service
from schemas.tasks import TaskCreateSchema, TaskSchema, TaskUpdateSchema
from services.task import TaskNotFound, TaskService


router = APIRouter(prefix="/tasks")

TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


@router.get("")
def get_tasks(task_service: TaskServiceDep) -> list[TaskSchema]:
    return task_service.get_tasks()


@router.get("/{task_id}")
def get_task(task_id: str, task_service: TaskServiceDep) -> TaskSchema:
    try:
        return task_service.get_task(task_id)
    except TaskNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreateSchema, task_service: TaskServiceDep
) -> TaskSchema:
    return task_service.create_task(payload)


@router.patch("/{task_id}")
def update_task(
    task_id: str, payload: TaskUpdateSchema, task_service: TaskServiceDep
) -> TaskSchema:
    try:
        return task_service.update_task(task_id, payload)
    except TaskNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from None


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, task_service: TaskServiceDep) -> None:
    try:
        task_service.delete_task(task_id)
    except TaskNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        ) from None


