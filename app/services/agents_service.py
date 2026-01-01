from sqlalchemy.exc import IntegrityError
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.repositories.agents_repo import AgentsRepository
from app.repositories.tools_repo import ToolsRepository


class AgentsService:
    def __init__(self, agents_repo: AgentsRepository, tools_repo: ToolsRepository):
        self.agents_repo = agents_repo
        self.tools_repo = tools_repo

    def create(self, tenant_id: str, payload):
        tools = []
        if payload.tool_ids:
            tools = self.tools_repo.get_many(tenant_id, payload.tool_ids)
            if len(tools) != len(set(payload.tool_ids)):
                raise BadRequestError("One or more tools not found for this tenant")

        try:
            return self.agents_repo.create(
                tenant_id=tenant_id,
                name=payload.name,
                role=payload.role,
                description=payload.description,
                tools=tools,
            )
        except IntegrityError:
            raise ConflictError("Agent name already exists for this tenant")

    def list(self, tenant_id: str, tool_name: str | None):
        return self.agents_repo.list(tenant_id, tool_name)

    def get(self, tenant_id: str, agent_id: int):
        agent = self.agents_repo.get(tenant_id, agent_id)
        if not agent:
            raise NotFoundError("Agent not found")
        return agent

    def update(self, tenant_id: str, agent_id: int, payload):
        agent = self.get(tenant_id, agent_id)

        if payload.name is not None:
            agent.name = payload.name
        if payload.role is not None:
            agent.role = payload.role
        if payload.description is not None:
            agent.description = payload.description

        if payload.tool_ids is not None:
            if payload.tool_ids:
                tools = self.tools_repo.get_many(tenant_id, payload.tool_ids)
                if len(tools) != len(set(payload.tool_ids)):
                    raise BadRequestError("One or more tools not found for this tenant")
                agent.tools = tools
            else:
                agent.tools = []

        try:
            self.agents_repo.save()
        except IntegrityError:
            raise ConflictError("Agent name already exists for this tenant")

        return agent

    def delete(self, tenant_id: str, agent_id: int) -> None:
        agent = self.get(tenant_id, agent_id)
        self.agents_repo.delete(agent)
