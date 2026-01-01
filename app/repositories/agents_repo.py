from sqlalchemy.orm import Session
from app.db.models import Agent, Tool


class AgentsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, tenant_id: str, name: str, role: str, description: str, tools: list[Tool]
    ) -> Agent:
        agent = Agent(
            tenant_id=tenant_id,
            name=name,
            role=role,
            description=description,
        )
        agent.tools = tools
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def list(self, tenant_id: str, tool_name: str | None = None) -> list[Agent]:
        q = self.db.query(Agent).filter(Agent.tenant_id == tenant_id)

        if tool_name:
            q = (
                q.join(Agent.tools)
                .filter(Tool.tenant_id == tenant_id, Tool.name == tool_name)
                .distinct()
            )

        return q.order_by(Agent.id.asc()).all()

    def get(self, tenant_id: str, agent_id: int) -> Agent | None:
        return (
            self.db.query(Agent)
            .filter(Agent.tenant_id == tenant_id, Agent.id == agent_id)
            .first()
        )

    def save(self) -> None:
        self.db.commit()

    def delete(self, agent: Agent) -> None:
        self.db.delete(agent)
        self.db.commit()
