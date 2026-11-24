from sqlalchemy.orm import Session

from cache.redis import RedisCache
from repositories.task import TaskRepository
from schemas.tasks import TaskCreateSchema, TaskSchema, TaskUpdateSchema

class TaskNotFound(Exception):
    pass

class TaskService:
    def __init__(self, db: Session, cache: RedisCache, cache_tasks_key: str):
        self.db = db
        self.tasks_repository = TaskRepository(db)
        self.cache = cache
        self.cache_tasks_key = cache_tasks_key

    def get_tasks(self) -> list[TaskSchema]:
        # Проверить кэш в redis, если есть вернуть
        cache_tasks = self.cache.get(self.cache_tasks_key)
        
        if cache_tasks is not None:
            return [TaskSchema.model_validate(task) for task in cache_tasks]
        
        tasks_orm = self.tasks_repository.get_all() 
        tasks_read = [TaskSchema.model_validate(task) for task in tasks_orm]

        # Преобразует в dict 
        tasks_for_cache = [task.model_dump(mode='json') for task in tasks_read]

        # Сохраняет в redis 
        self.cache.set(self.cache_tasks_key, tasks_for_cache)
        return tasks_read

    def create_task(self, task_create: TaskCreateSchema) -> TaskSchema:
        # Инвалидация кэша
        self.cache.delete(self.cache_tasks_key)

        task_orm = self.tasks_repository.create(task_create.title)
        self.db.commit()
        return TaskSchema.model_validate(task_orm)

    def get_task(self, task_id: str) -> TaskSchema:
        task_orm = self.tasks_repository.get_by_id(task_id)

        if task_orm is None:
            raise TaskNotFound("Task not found")

        return TaskSchema.model_validate(task_orm)

    def update_task(self, task_id: str, task_update: TaskUpdateSchema) -> TaskSchema:
        task_orm = self.tasks_repository.get_by_id(task_id)

        if task_orm is None:
            raise TaskNotFound("Task not found")

        if task_update.title is not None:
            task_orm.title = task_update.title
        if task_update.completed is not None:
            task_orm.completed = task_update.completed

        self.db.commit()
        self.db.refresh(task_orm)

        # Инвалидация кэша
        self.cache.delete(self.cache_tasks_key)
        return TaskSchema.model_validate(task_orm)

    def delete_task(self, task_id: str) -> None:
        task = self.tasks_repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFound("Task not found")

        self.tasks_repository.delete(task)
        self.db.commit()
        # Инвалидация кэша
        self.cache.delete(self.cache_tasks_key)
