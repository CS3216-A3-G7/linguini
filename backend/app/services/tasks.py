from uuid import UUID

from app.repositories.tasks import TaskNotFoundError, TaskRepository
from app.schemas.tasks import SessionTaskPublic
from app.services.users import UserService


class TaskService:
    def __init__(self, repository: TaskRepository, users: UserService, engine=None) -> None:
        self.repository = repository
        self.users = users
        self.engine = engine

    def get(self, task_id: UUID) -> SessionTaskPublic:
        task = self.repository.get(task_id, self.users.get_current_user().id)
        if task is None:
            raise TaskNotFoundError("Task not found.")
        return SessionTaskPublic.from_internal(task)

    def action(self, task_id, action, request=None):
        from app.repositories.postgres.workflow import PostgresWorkflowRepository

        user = self.users.get_current_user()
        return PostgresWorkflowRepository(self.engine, user.id).task_action(
            task_id, action, request
        )
