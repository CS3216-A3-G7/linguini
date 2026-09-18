from uuid import UUID

from app.repositories.tasks import TaskNotFoundError, TaskRepository
from app.schemas.tasks import SessionTaskPublic
from app.services.users import UserService


class TaskService:
    def __init__(self, repository: TaskRepository, users: UserService) -> None:
        self.repository = repository
        self.users = users

    def get(self, task_id: UUID) -> SessionTaskPublic:
        task = self.repository.get(task_id, self.users.get_current_user().id)
        if task is None:
            raise TaskNotFoundError("Task not found.")
        return SessionTaskPublic.from_internal(task)
