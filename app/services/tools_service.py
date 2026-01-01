from sqlalchemy.exc import IntegrityError
from app.core.errors import NotFoundError, ConflictError
from app.repositories.tools_repo import ToolsRepository


class ToolsService:
    def __init__(self, repo: ToolsRepository):
        self.repo = repo

    def create(self, tenant_id: str, name: str, description: str):
        try:
            return self.repo.create(tenant_id, name, description)
        except IntegrityError:
            raise ConflictError("Tool name already exists for this tenant")

    def list(self, tenant_id: str):
        return self.repo.list_tools(tenant_id)

    def get(self, tenant_id: str, tool_id: int):
        tool = self.repo.get(tenant_id, tool_id)
        if not tool:
            raise NotFoundError("Tool not found")
        return tool

    def update(
        self, tenant_id: str, tool_id: int, name: str | None, description: str | None
    ):
        tool = self.get(tenant_id, tool_id)

        if name is not None:
            tool.name = name
        if description is not None:
            tool.description = description

        try:
            self.repo.save()
        except IntegrityError:
            raise ConflictError("Tool name already exists for this tenant")

        return tool

    def delete(self, tenant_id: str, tool_id: int) -> None:
        tool = self.get(tenant_id, tool_id)
        self.repo.delete(tool)
