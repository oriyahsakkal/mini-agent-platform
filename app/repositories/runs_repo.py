from sqlalchemy.orm import Session
from app.db.models import AgentExecution


class RunsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        tenant_id: str,
        agent_id: int,
        model: str,
        prompt: str,
        response: str,
    ) -> AgentExecution:
        execution = AgentExecution(
            tenant_id=tenant_id,
            agent_id=agent_id,
            model=model,
            prompt=prompt,
            response=response,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def list(
        self,
        tenant_id: str,
        agent_id: int,
        limit: int,
        offset: int,
    ) -> tuple[int, list[AgentExecution]]:
        q = (
            self.db.query(AgentExecution)
            .filter(
                AgentExecution.tenant_id == tenant_id,
                AgentExecution.agent_id == agent_id,
            )
            .order_by(AgentExecution.created_at.desc())
        )

        total = q.count()
        items = q.offset(offset).limit(limit).all()
        return total, items
