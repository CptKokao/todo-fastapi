from app.repositories.task import TaskRepository
from app.schemas.tasks import TaskSchema,TaskCreateSchema, TaskUpdateSchema

class TaskNotFound(Exception):
    pass

class TaskService:
    def __init__(self, db):
        self.db = db
        self.tasks_repository = TaskRepository(db)

    def get_tasks(self) -> list[TaskSchema]:
        tasks_orm = self.tasks_repository.get_all()
        print('___________________________________--')
        return [TaskSchema.model_validate(task) for task in tasks_orm]

    def create_task(self, task_create: TaskCreateSchema) -> TaskSchema:
        task_orm = self.tasks_repository.create(task_create.title)
        self.db.commit()
        return TaskSchema.model_validate(task_orm)

    def update_task(self, task_id: str, task_update: TaskUpdateSchema) -> TaskSchema:
        try:
            tasks_orm = self.tasks_repository.get_by_id(task_id)
        except Exception:
            raise TaskNotFound("Task not found")

        if task_update.title:
            tasks_orm.title = task_update.title
        if task_update.completed is not None:
            tasks_orm.completed = task_update.completed

        self.db.commit()
        return TaskSchema.model_validate(tasks_orm)

    def delete_task(self, task_id: str) -> None:
        task = self.tasks_repository.get_by_id(task_id)

        if task is None:
            raise TaskNotFound("Task not found")

        self.tasks_repository.delete(task)
        self.db.commit()
